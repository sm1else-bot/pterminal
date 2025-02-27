import logging
import random
from flask import render_template, request, jsonify, session
from app import app, db
from models import Trainer, Pokemon, Pokedex
from game_logic import GameLogic
import json

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/start-game', methods=['POST'])
def start_game():
    data = request.json
    trainer_name = data.get('trainer_name')
    starter_choice = data.get('starter_choice')
    logger.debug(f"Starting game for trainer: {trainer_name}, starter: {starter_choice}")

    # Check if trainer name exists
    existing_trainer = Trainer.query.filter_by(name=trainer_name).first()
    
    try:
        if existing_trainer:
            # Log in existing trainer
            trainer = existing_trainer
            logger.debug(f"Logging in existing trainer {trainer_name} with ID: {trainer.id}")
            
            # Get the trainer's Pokémon
            trainer_pokemon = Pokemon.query.filter_by(trainer_id=trainer.id).first()
            if not trainer_pokemon:
                logger.error(f"No Pokemon found for trainer {trainer_name}")
                return jsonify({'status': 'error', 'message': 'No Pokémon found for this trainer'})
            
            logger.debug(f"Loaded existing Pokémon ID: {trainer_pokemon.pokemon_id} for trainer {trainer_name}")
        else:
            # Create new trainer
            trainer = Trainer(name=trainer_name)
            db.session.add(trainer)
            db.session.commit()
            logger.debug(f"Created new trainer with ID: {trainer.id}")

            # Add starter Pokémon
            starter_ids = {'charmander': 4, 'squirtle': 7, 'bulbasaur': 1}
            starter = GameLogic.create_new_pokemon(trainer.id, starter_ids[starter_choice])
            if not starter:
                logger.error("Failed to create starter Pokemon")
                return jsonify({'status': 'error', 'message': 'Failed to create starter Pokemon'})

            db.session.add(starter)

            # Initialize Pokédex entry
            pokedex_entry = Pokedex(trainer_id=trainer.id, pokemon_id=starter_ids[starter_choice], caught=True)
            db.session.add(pokedex_entry)
            db.session.commit()

        session['trainer_id'] = trainer.id
        session['current_battle'] = None
        logger.debug(f"Session initialized with trainer_id: {trainer.id}")
        
        if existing_trainer:
            return jsonify({
                'status': 'success',
                'message': f'Welcome back, Trainer {trainer_name}! Type /hunt to start catching Pokémon!'
            })
        else:
            return jsonify({
                'status': 'success',
                'message': f'Welcome, Trainer {trainer_name}! Type /hunt to start catching Pokémon!'
            })
    except Exception as e:
        logger.error(f"Error in start_game: {str(e)}")
        db.session.rollback()
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/api/command', methods=['POST'])
def handle_command():
    if 'trainer_id' not in session:
        logger.debug("No active session found")
        return jsonify({'status': 'error', 'message': 'No active session'})

    data = request.json
    command = data.get('command', '').lower().split()
    base_command = command[0]
    args = command[1:] if len(command) > 1 else []
    trainer_id = session['trainer_id']

    logger.debug(f"Handling command: {base_command} with args: {args}")
    logger.debug(f"Current session state: {dict(session)}")

    if base_command == '/hunt':
        pokemon_id = GameLogic.generate_random_pokemon()
        pokemon_data = GameLogic.get_pokemon_data(pokemon_id)
        if pokemon_data:
            # Store just the ID in session instead of full data
            session['current_wild_pokemon_id'] = pokemon_id
            session['current_battle'] = None  # Reset any existing battle
            sprite_url = GameLogic.get_pokemon_sprite_url(pokemon_id)
            ev_yields = GameLogic.get_pokemon_ev_yields(pokemon_id)
            logger.debug(f"Wild Pokemon encountered: {pokemon_data['name']} (ID: {pokemon_id})")

            response_text = [
                f"A wild {pokemon_data['name'].capitalize()} appeared!",
                "",
                "Available commands:",
                "/battle - Start battle",
                "/evyield - Check EV yields"
            ]

            return jsonify({
                'status': 'success',
                'message': '\n'.join(response_text),
                'sprite_url': sprite_url,
                'pokemon': pokemon_data,
                'ev_yields': ev_yields
            })
        return jsonify({'status': 'error', 'message': 'Failed to find a Pokémon'})

    elif base_command == '/battle':
        if 'current_wild_pokemon_id' not in session:
            logger.debug("No wild Pokemon in session for battle")
            return jsonify({'status': 'error', 'message': 'No wild Pokémon to battle! Use /hunt first.'})

        # Fetch fresh data for the stored Pokemon ID
        wild_pokemon_data = GameLogic.get_pokemon_data(session['current_wild_pokemon_id'])
        if not wild_pokemon_data:
            logger.error("Failed to fetch wild Pokemon data")
            return jsonify({'status': 'error', 'message': 'Failed to start battle'})

        battle_state = GameLogic.initialize_battle(trainer_id, wild_pokemon_data)
        if not battle_state:
            logger.error("Failed to initialize battle state")
            return jsonify({'status': 'error', 'message': 'Failed to start battle'})

        session['current_battle'] = battle_state
        logger.debug("Battle initialized successfully")
        logger.debug(f"Battle state: {battle_state}")

        return jsonify({
            'status': 'success',
            'message': GameLogic.format_battle_state(battle_state),
            'battle_state': battle_state
        })

    elif base_command.startswith('/move'):
        logger.debug(f"Current battle state in session: {session.get('current_battle')}")
        if not session.get('current_battle'):
            return jsonify({'status': 'error', 'message': 'No active battle! Use /battle first.'})

        try:
            move_index = int(args[0]) - 1
            logger.debug(f"Executing move {move_index + 1}")

            current_battle = session['current_battle']
            battle_result = GameLogic.execute_turn(current_battle, move_index)
            logger.debug(f"Battle result: {battle_result}")

            if battle_result['status'] == 'success':
                session['current_battle'] = battle_result['battle_state']
                if battle_result.get('battle_ended'):
                    session['current_wild_pokemon_id'] = None
                    session['current_battle'] = None
                    logger.debug("Battle ended, cleared battle state")
            else:
                logger.error(f"Battle turn failed: {battle_result.get('message')}")

            # Prepare basic response
            response_data = {
                'status': battle_result['status'],
                'battle_state': battle_result.get('battle_state'),
                'battle_ended': battle_result.get('battle_ended', False)
            }
            
            # Set message content based on battle state
            if battle_result['status'] == 'success':
                if battle_result.get('battle_ended'):
                    # If battle ended, show only outcome message
                    response_data['message'] = battle_result['message']
                else:
                    # If battle continues, show only action results (first few lines) + current state
                    # Extract just the action results from the message (typically first 3-5 lines)
                    action_lines = battle_result['message'].split('\n')
                    action_message = '\n'.join([line for line in action_lines if not line.startswith('Choose your move')])
                    
                    # Get updated battle state display
                    updated_state = GameLogic.format_battle_state(battle_result['battle_state'])
                    
                    # Combine action message with current state
                    response_data['message'] = f"{action_message}\n\n{updated_state}"
            else:
                # For error messages, keep as is
                response_data['message'] = battle_result['message']
                
            return jsonify(response_data)

        except (IndexError, ValueError) as e:
            logger.error(f"Invalid move number: {e}")
            return jsonify({'status': 'error', 'message': 'Invalid move number!'})
        except Exception as e:
            logger.error(f"Unexpected error in move execution: {e}")
            return jsonify({'status': 'error', 'message': 'Battle execution failed'})

    elif base_command == '/catch':
        if 'current_battle' not in session or not session['current_battle']:
            return jsonify({'status': 'error', 'message': 'No active battle! Start a battle first with /battle.'})
        
        battle_state = session['current_battle']
        wild_pokemon = battle_state['wild_pokemon']
        
        # Check if HP is below half
        current_hp = wild_pokemon['current_hp']
        max_hp = wild_pokemon['max_hp']
        
        if current_hp > max_hp / 2:
            return jsonify({
                'status': 'error', 
                'message': f"Wild {wild_pokemon['name'].capitalize()}'s HP is too high ({current_hp}/{max_hp})! Weaken it further to catch."
            })
        
        # Calculate catch factor based on remaining HP percentage
        hp_percentage = current_hp / max_hp * 100
        
        if hp_percentage > 50:
            catch_factor = 0  # Should not reach here due to above check
        elif 40 <= hp_percentage <= 50:
            catch_factor = 1.0
        elif 30 <= hp_percentage < 40:
            catch_factor = 1.2
        elif 15 <= hp_percentage < 30:
            catch_factor = 1.5
        elif 5 <= hp_percentage < 15:
            catch_factor = 1.8
        else:
            catch_factor = 2.0
        
        # Calculate catch probability (base 50%)
        catch_probability = 50 * catch_factor
        
        # Random roll for catch success
        roll = random.randint(1, 100)
        
        if roll <= catch_probability:
            # Catch successful
            pokemon_id = session['current_wild_pokemon_id']
            trainer_id = session['trainer_id']
            
            try:
                # Create captured Pokémon
                new_pokemon = GameLogic.create_new_pokemon(trainer_id, pokemon_id, level=wild_pokemon['level'])
                db.session.add(new_pokemon)
                
                # Add Pokédex entry if not already caught
                pokedex_entry = Pokedex.query.filter_by(trainer_id=trainer_id, pokemon_id=pokemon_id).first()
                if not pokedex_entry:
                    pokedex_entry = Pokedex(trainer_id=trainer_id, pokemon_id=pokemon_id, caught=True)
                    db.session.add(pokedex_entry)
                else:
                    pokedex_entry.caught = True
                
                db.session.commit()
                
                # Clear battle state
                session['current_wild_pokemon_id'] = None
                session['current_battle'] = None
                
                pokemon_data = GameLogic.get_pokemon_data(pokemon_id)
                return jsonify({
                    'status': 'success',
                    'message': f"Gotcha! {pokemon_data['name'].capitalize()} was caught!",
                    'battle_ended': True
                })
                
            except Exception as e:
                logger.error(f"Error catching Pokemon: {str(e)}")
                db.session.rollback()
                return jsonify({'status': 'error', 'message': 'Failed to catch Pokémon due to an error.'})
        else:
            # Catch failed
            return jsonify({
                'status': 'error',
                'message': f"Oh no! {wild_pokemon['name'].capitalize()} broke free! (Roll: {roll}, Needed: {catch_probability:.1f})"
            })
            
    elif base_command == '/evyield':
        if 'current_wild_pokemon_id' not in session:
            return jsonify({'status': 'error', 'message': 'No wild Pokémon to check! Use /hunt first.'})

        ev_yields = GameLogic.get_pokemon_ev_yields(session['current_wild_pokemon_id'])
        return jsonify({
            'status': 'success',
            'message': GameLogic.format_ev_yields(ev_yields)
        })

    elif base_command == '/mypokemon':
        pokemon_list = Pokemon.query.filter_by(trainer_id=trainer_id).all()
        pokemon_data = []
        for pokemon in pokemon_list:
            poke_info = GameLogic.get_pokemon_data(pokemon.pokemon_id)
            if poke_info:
                pokemon_data.append({
                    'name': poke_info['name'],
                    'level': pokemon.level,
                    'nature': pokemon.nature,
                    'moves': pokemon.get_moves()
                })
        return jsonify({
            'status': 'success',
            'pokemon': pokemon_data
        })

    elif base_command == '/mystats':
        trainer = Trainer.query.get(trainer_id)
        return jsonify({
            'status': 'success',
            'stats': {
                'name': trainer.name,
                'pokedollars': trainer.pokedollars,
                'pokemon_count': len(trainer.pokemon)
            }
        })

    return jsonify({'status': 'error', 'message': 'Unknown command'})