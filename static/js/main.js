function startGame() {
    const trainerName = document.getElementById('trainer-name').value;
    const starterChoice = document.querySelector('input[name="starter"]:checked')?.value; // Handle case where no starter is selected

    console.log("Starting game with:", { trainerName, starterChoice });

    fetch('/api/start-game', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            trainer_name: trainerName,
            starter_choice: starterChoice
        })
    })
    .then(response => response.json())
    .then(data => {
        console.log("Game start response:", data);

        if (data.status === 'success') {
            document.getElementById('setup-form').style.display = 'none';
            document.getElementById('game-interface').style.display = 'block';

            // Display welcome message
            addToConsole(data.message);

            // Focus command input
            document.getElementById('command-input').focus();
        } else if (data.status === 'existing_user') {
            // Existing user, log in and load their pokemon
            document.getElementById('setup-form').style.display = 'none';
            document.getElementById('game-interface').style.display = 'block';
            addToConsole(`Welcome back, ${data.trainer_name}! Your team has been loaded.`);
            //Further actions to load the pokemon should be added here.  This would require additional backend and frontend logic.
            document.getElementById('command-input').focus();
        } else {
            // Show error message
            alert(data.message);
        }
    })
    .catch(error => {
        console.error('Error starting game:', error);
        alert('Error starting game. Please try again.');
    });
}