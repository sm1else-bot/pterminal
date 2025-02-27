class Terminal {
    constructor(containerId) {
        this.container = document.getElementById(containerId);
        this.history = [];
        this.initializeTerminal();
    }

    initializeTerminal() {
        this.terminal = document.createElement('div');
        this.terminal.className = 'terminal-content';
        this.container.appendChild(this.terminal);

        this.input = document.createElement('input');
        this.input.type = 'text';
        this.input.className = 'terminal-input form-control';
        this.input.placeholder = 'Enter command...';
        this.container.appendChild(this.input);

        this.input.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.handleCommand(this.input.value);
                this.input.value = '';
            }
        });
    }

    print(message, className = '') {
        const lines = message.split('\n');
        lines.forEach(line => {
            const lineElement = document.createElement('div');
            lineElement.className = `terminal-line ${className}`;
            lineElement.textContent = line;
            this.terminal.appendChild(lineElement);
        });
        this.scrollToBottom();
    }

    displaySprite(url) {
        const imgContainer = document.createElement('div');
        imgContainer.className = 'terminal-line pokemon-sprite';
        const img = document.createElement('img');
        img.src = url;
        img.alt = 'Pokemon Sprite';
        img.onerror = () => {
            console.error('Failed to load sprite:', url);
            this.print('Failed to load Pokemon sprite', 'error');
        };
        imgContainer.appendChild(img);
        this.terminal.appendChild(imgContainer);
        this.scrollToBottom();
    }

    scrollToBottom() {
        requestAnimationFrame(() => {
            this.terminal.scrollTop = this.terminal.scrollHeight;
        });
    }

    async handleCommand(command) {
        this.print(`> ${command}`, 'command');

        try {
            const response = await fetch('/api/command', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ command: command })
            });

            // Check if the response is valid JSON
            const text = await response.text();
            let data;
            try {
                data = JSON.parse(text);
            } catch (e) {
                console.error("Invalid JSON response:", text);
                this.print("Error: Server returned an invalid response. Please try again.", "error");
                return;
            }

            if (data.status === 'success') {
                if (data.sprite_url) {
                    this.displaySprite(data.sprite_url);
                }

                if (command === '/mypokemon' && data.pokemon) {
                    data.pokemon.forEach(pokemon => {
                        const movesList = pokemon.moves ? `\n  Moves: ${pokemon.moves.join(', ')}` : '';
                        this.print(`${pokemon.name.toUpperCase()} (Lv. ${pokemon.level}) - ${pokemon.nature}${movesList}`);
                    });
                } else if (command === '/mystats' && data.stats) {
                    this.print(`Trainer: ${data.stats.name}`);
                    this.print(`PokéDollars: ${data.stats.pokedollars}`);
                    this.print(`Pokémon: ${data.stats.pokemon_count}`);
                } else if (command === '/hunt' && data.pokemon) {
                    this.print(data.message);
                } else if (command === '/battle' && data.battle_state) {
                    this.print(data.message);
                    if (data.battle_state.turn === 'player') {
                        this.print('\nChoose your move (type /move <number>)');
                    }
                } else if (command.startsWith('/move') && data.battle_state) {
                    this.print(data.message);
                    if (!data.battle_ended && data.battle_state.turn === 'player') {
                        this.print('\nChoose your move (type /move <number>)');
                    }
                } else {
                    this.print(data.message);
                }
            } else {
                this.print(`Error: ${data.message}`, 'error');
            }
        } catch (error) {
            console.error('Error:', error);
            this.print('An error occurred while processing the command', 'error');
        }
    }
}

// Initialize game
document.addEventListener('DOMContentLoaded', () => {
    const terminal = new Terminal('terminal');

    const startGame = async (trainerName, starterChoice) => {
        try {
            console.log('Starting game with:', { trainerName, starterChoice });
            const response = await fetch('/api/start-game', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ trainer_name: trainerName, starter_choice: starterChoice })
            });

            // Safer JSON parsing
            const text = await response.text();
            let data;
            try {
                data = JSON.parse(text);
                console.log('Game start response:', data);
            } catch (e) {
                console.error("Invalid JSON response:", text);
                terminal.print("Error: Server returned an invalid response. Please try again.", "error");
                return;
            }

            if (data.status === 'success') {
                // Check if it's a welcome back message
                terminal.print(data.message);
                document.getElementById('setup-form').style.display = 'none';
                terminal.scrollToBottom();
            } else {
                terminal.print(`Error: ${data.message}`, 'error');
            }
        } catch (error) {
            console.error('Error details:', error);
            terminal.print('Error starting game. Please try again.', 'error');
        }
    };

    // Handle new game setup
    const setupForm = document.getElementById('setup-form');
    if (setupForm) {
        setupForm.addEventListener('submit', (e) => {
            e.preventDefault();
            const trainerName = document.getElementById('trainer-name').value;
            const starterChoice = document.querySelector('input[name="starter"]:checked').value;
            startGame(trainerName, starterChoice);
        });
    }
});