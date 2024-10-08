let canvas = document.getElementById('game-canvas');
let ctx = canvas.getContext('2d');
let score = 0;
let timeLeft = 60;
let gameInterval;
let moles = [];
let gameMode = 'single';
let difficulty = 'easy';

const difficultySettings = {
    easy: { spawnRate: 1500, duration: 2000 },
    medium: { spawnRate: 1000, duration: 1500 },
    hard: { spawnRate: 750, duration: 1000 }
};

document.getElementById('single-player').addEventListener('click', () => setGameMode('single'));
document.getElementById('ai-player').addEventListener('click', () => setGameMode('ai'));

document.querySelectorAll('.difficulty-button').forEach(button => {
    button.addEventListener('click', (e) => setDifficulty(e.target.dataset.difficulty));
});

document.getElementById('start-button').addEventListener('click', startGame);

function setGameMode(mode) {
    gameMode = mode;
    document.querySelectorAll('.mode-button').forEach(btn => btn.classList.remove('selected'));
    document.getElementById(`${mode}-player`).classList.add('selected');
}

function setDifficulty(level) {
    difficulty = level;
    document.querySelectorAll('.difficulty-button').forEach(btn => btn.classList.remove('selected'));
    document.querySelector(`[data-difficulty="${level}"]`).classList.add('selected');
}

function startGame() {
    score = 0;
    timeLeft = 60;
    moles = [];
    updateScore();
    updateTime();

    clearInterval(gameInterval);
    gameInterval = setInterval(() => {
        timeLeft--;
        updateTime();
        if (timeLeft <= 0) {
            endGame();
        }
    }, 1000);

    canvas.addEventListener('click', handleClick);
    spawnMole();
}

function spawnMole() {
    let x = Math.random() * (canvas.width - 50);
    let y = Math.random() * (canvas.height - 50);
    let mole = { x, y, active: true };
    moles.push(mole);
    drawMole(mole);

    setTimeout(() => {
        mole.active = false;
        if (gameMode === 'ai') {
            aiMove();
        }
    }, difficultySettings[difficulty].duration);

    setTimeout(spawnMole, difficultySettings[difficulty].spawnRate);
}

function drawMole(mole) {
    ctx.fillStyle = mole.active ? 'brown' : '#8FBC8F';
    ctx.beginPath();
    ctx.arc(mole.x + 25, mole.y + 25, 25, 0, 2 * Math.PI);
    ctx.fill();
}

function handleClick(event) {
    let rect = canvas.getBoundingClientRect();
    let x = event.clientX - rect.left;
    let y = event.clientY - rect.top;

    moles.forEach(mole => {
        if (mole.active && Math.sqrt((x - (mole.x + 25))**2 + (y - (mole.y + 25))**2) < 25) {
            mole.active = false;
            score++;
            updateScore();
        }
    });
}

function aiMove() {
    fetch('/ai_move', { method: 'POST' })
        .then(response => response.json())
        .then(data => {
            moles.forEach(mole => {
                if (mole.active && Math.sqrt((data.x - (mole.x + 25))**2 + (data.y - (mole.y + 25))**2) < 25) {
                    mole.active = false;
                }
            });
        });
}

function updateScore() {
    document.getElementById('score-value').textContent = score;
}

function updateTime() {
    document.getElementById('time-value').textContent = timeLeft;
}

function endGame() {
    clearInterval(gameInterval);
    canvas.removeEventListener('click', handleClick);
    alert(`Game Over! Your score: ${score}`);

    if (gameMode === 'single') {
        submitScore(score, difficulty);
    }
}

function submitScore(score, difficulty) {
    fetch('/submit_score', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ score: score, difficulty: difficulty }),
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Failed to submit score');
        }
        return response.json();
    })
    .then(data => {
        console.log('Score submitted successfully:', data);
    })
    .catch(error => {
        console.error('Error submitting score:', error);
        alert('Error: ' + error.message);
    });
}

function gameLoop() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    moles.forEach(drawMole);
    requestAnimationFrame(gameLoop);
}

gameLoop();