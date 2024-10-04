const canvas = document.getElementById('game-canvas');
const ctx = canvas.getContext('2d');
const startScreen = document.getElementById('start-screen');
const gameScreen = document.getElementById('game-screen');
const gameOverScreen = document.getElementById('game-over-screen');
const startButton = document.getElementById('start-button');
const restartButton = document.getElementById('restart-button');
const scoreValue = document.getElementById('score-value');
const timeValue = document.getElementById('time-value');
const finalScore = document.getElementById('final-score');
const gameResult = document.getElementById('game-result');
const difficultyButtons = document.querySelectorAll('.difficulty-button');

const CANVAS_WIDTH = 600;
const CANVAS_HEIGHT = 400;
const GRID_SIZE = 3;
const HOLE_SIZE = 100;
const MOLE_SIZE = 80;

canvas.width = CANVAS_WIDTH;
canvas.height = CANVAS_HEIGHT;

let timeLeft;
let gameInterval;
let moles = [];
let debugMode = false;
let lastFrameTime = 0;
let firstMoleAppeared = false;
let lastMoleAppearance = 0;
let selectedDifficulty = null;
let powerUps = [];
let activePowerUp = null;
let powerUpDuration = 3000;
let lastPowerUpSpawn = 0;

let currentPlayer = 1;
let player1Score = 0;
let player2Score = 0;

const holeImage = new Image();
holeImage.src = '/static/assets/hole.svg';

const moleImage = new Image();
moleImage.src = '/static/assets/mole.svg';

const fastMoleImage = new Image();
fastMoleImage.src = '/static/assets/fast_mole.svg';

const goldenMoleImage = new Image();
goldenMoleImage.src = '/static/assets/golden_mole.svg';

const hammerImage = new Image();
hammerImage.src = '/static/assets/hammer.svg';

function loadAudio(src) {
    return new Promise((resolve, reject) => {
        const audio = new Audio(src);
        audio.oncanplaythrough = () => resolve(audio);
        audio.onerror = reject;
    });
}

let whackSound, moleAppearSound, gameOverSound, winSound;

Promise.all([
    loadAudio('/static/assets/whack.mp3'),
    loadAudio('/static/assets/mole_appear.mp3'),
    loadAudio('/static/assets/game_over.mp3'),
    loadAudio('/static/assets/win.mp3')
]).then(([whack, moleAppear, gameOver, win]) => {
    whackSound = whack;
    moleAppearSound = moleAppear;
    gameOverSound = gameOver;
    winSound = win;
    console.log('All audio files loaded successfully');
}).catch(error => {
    console.error('Error loading audio files:', error);
    whackSound = moleAppearSound = gameOverSound = winSound = { play: () => {} };
});

function updateScore(points) {
    const maxScore = 1000000;
    if (currentPlayer === 1) {
        player1Score = Math.min(player1Score + points, maxScore);
    } else {
        player2Score = Math.min(player2Score + points, maxScore);
    }
    scoreValue.textContent = `P1: ${player1Score} | P2: ${player2Score}`;
}

class Mole {
    constructor(x, y) {
        this.x = x;
        this.y = y;
        this.visible = false;
        this.lastAppearance = 0;
        this.setType('normal');
    }

    setType(type) {
        this.type = type;
        switch (type) {
            case 'fast':
                this.appearDuration = 1000;
                this.points = 2;
                this.image = fastMoleImage;
                break;
            case 'golden':
                this.appearDuration = 750;
                this.points = 5;
                this.image = goldenMoleImage;
                break;
            default:
                this.appearDuration = 2000;
                this.points = 1;
                this.image = moleImage;
        }
    }

    draw() {
        ctx.drawImage(holeImage, this.x - HOLE_SIZE / 2, this.y - HOLE_SIZE / 2, HOLE_SIZE, HOLE_SIZE);
        if (this.visible) {
            ctx.drawImage(this.image, this.x - MOLE_SIZE / 2, this.y - MOLE_SIZE / 2, MOLE_SIZE, MOLE_SIZE);
        }
        if (debugMode) {
            ctx.fillStyle = this.visible ? 'green' : 'red';
            ctx.fillRect(this.x - 5, this.y - 5, 10, 10);
            if (this.visible) {
                ctx.fillStyle = 'white';
                ctx.font = '12px Arial';
                ctx.fillText(this.type, this.x - 15, this.y + 30);
            }
        }
    }

    hit() {
        if (this.visible) {
            this.visible = false;
            updateScore(this.points);
            whackSound.play();
            return true;
        }
        return false;
    }
}

class PowerUp {
    constructor(x, y, type) {
        this.x = x;
        this.y = y;
        this.visible = true;
        this.type = type;
        this.size = 40;
        this.appearDuration = 5000;
        this.lastAppearance = Date.now();
    }

    draw() {
        ctx.fillStyle = this.type === 'hammer' ? 'red' : 'blue';
        ctx.beginPath();
        ctx.arc(this.x, this.y, this.size / 2, 0, 2 * Math.PI);
        ctx.fill();
        ctx.fillStyle = 'white';
        ctx.font = '20px Arial';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillText(this.type === 'hammer' ? 'H' : 'F', this.x, this.y);
    }
}

function initializeMoles() {
    moles = [];
    for (let row = 0; row < GRID_SIZE; row++) {
        for (let col = 0; col < GRID_SIZE; col++) {
            const x = (col + 0.5) * (CANVAS_WIDTH / GRID_SIZE);
            const y = (row + 0.5) * (CANVAS_HEIGHT / GRID_SIZE);
            moles.push(new Mole(x, y));
        }
    }
    console.log('Moles initialized:', moles);
}

function drawMoles() {
    moles.forEach(mole => mole.draw());
}

function getDifficultySettings(gameTime) {
    switch (selectedDifficulty) {
        case 'easy':
            if (gameTime <= 7) {
                return { maxVisibleMoles: 1, maxAppearDuration: 2000, scoreToWin: 30, gameDuration: 60 };
            } else if (gameTime <= 16) {
                return { maxVisibleMoles: 2, maxAppearDuration: 1520, scoreToWin: 30, gameDuration: 60 };
            } else {
                return { maxVisibleMoles: 1, maxAppearDuration: 920, scoreToWin: 30, gameDuration: 60 };
            }
        case 'medium':
            if (gameTime <= 7) {
                return { maxVisibleMoles: 1, maxAppearDuration: 1000, scoreToWin: 50, gameDuration: 45 };
            } else if (gameTime <= 16) {
                return { maxVisibleMoles: 2, maxAppearDuration: 1000, scoreToWin: 50, gameDuration: 45 };
            } else {
                return { maxVisibleMoles: 1, maxAppearDuration: 500, scoreToWin: 50, gameDuration: 45 };
            }
        case 'hard':
            if (gameTime <= 4) {
                return { maxVisibleMoles: 1, maxAppearDuration: 1500, scoreToWin: 80, gameDuration: 30 };
            } else if (gameTime <= 14) {
                return { maxVisibleMoles: 2, maxAppearDuration: 910, scoreToWin: 80, gameDuration: 30 };
            } else {
                return { maxVisibleMoles: 2, maxAppearDuration: 500, scoreToWin: 80, gameDuration: 30 };
            }
        default:
            console.error('Invalid difficulty level');
            return { maxVisibleMoles: 1, maxAppearDuration: 2000, scoreToWin: 30, gameDuration: 60 };
    }
}

function updateMoles(deltaTime) {
    const now = Date.now();
    const gameTime = getDifficultySettings().gameDuration - timeLeft;
    let { maxVisibleMoles, maxAppearDuration } = getDifficultySettings(gameTime);

    const visibleMoles = moles.filter(mole => mole.visible).length;

    if (visibleMoles < maxVisibleMoles) {
        const availableMoles = moles.filter(mole => !mole.visible);
        if (availableMoles.length > 0) {
            const spawnChance = (maxVisibleMoles - visibleMoles) * 0.2;
            if (Math.random() < spawnChance) {
                const randomMole = availableMoles[Math.floor(Math.random() * availableMoles.length)];
                randomMole.visible = true;
                randomMole.lastAppearance = now;

                const typeRoll = Math.random();
                if (typeRoll < 0.1) {
                    randomMole.setType('golden');
                } else if (typeRoll < 0.3) {
                    randomMole.setType('fast');
                } else {
                    randomMole.setType('normal');
                }

                moleAppearSound.play();
                lastMoleAppearance = now;
                console.log(`${randomMole.type} Mole appeared at: (${randomMole.x}, ${randomMole.y}), Time: ${now}, Game Time: ${gameTime.toFixed(2)}s, Appear Duration: ${randomMole.appearDuration}ms`);
            }
        }
    }

    moles.forEach(mole => {
        if (mole.visible && now - mole.lastAppearance > maxAppearDuration) {
            mole.visible = false;
            console.log(`${mole.type} Mole disappeared at: (${mole.x}, ${mole.y}), Time: ${now}, Duration: ${now - mole.lastAppearance}ms`);
        }
    });

    console.log(`Moles updated, visible moles: ${visibleMoles}, Game Time: ${gameTime.toFixed(2)}s, Max Visible: ${maxVisibleMoles}, Max Appear Duration: ${maxAppearDuration}ms`);
}

function updatePowerUps(now) {
    powerUps = powerUps.filter(powerUp => now - powerUp.lastAppearance <= powerUp.appearDuration);

    if (powerUps.length === 0 && now - lastPowerUpSpawn > 15000) {
        const type = Math.random() < 0.5 ? 'hammer' : 'freeze';
        const x = Math.random() * (CANVAS_WIDTH - 40) + 20;
        const y = Math.random() * (CANVAS_HEIGHT - 40) + 20;
        powerUps.push(new PowerUp(x, y, type));
        lastPowerUpSpawn = now;
    }

    if (activePowerUp && now - activePowerUp.startTime > powerUpDuration) {
        activePowerUp = null;
    }
}

function drawPowerUps() {
    powerUps.forEach(powerUp => powerUp.draw());
}

function collectPowerUp(x, y) {
    const index = powerUps.findIndex(powerUp => {
        const distance = Math.sqrt((x - powerUp.x) ** 2 + (y - powerUp.y) ** 2);
        return distance < powerUp.size / 2;
    });

    if (index !== -1) {
        const collectedPowerUp = powerUps[index];
        powerUps.splice(index, 1);
        activePowerUp = {
            type: collectedPowerUp.type,
            startTime: Date.now()
        };
        console.log(`Power-up collected: ${collectedPowerUp.type}`);
    }
}

function applyPowerUpEffects() {
    if (!activePowerUp) return;

    if (activePowerUp.type === 'hammer') {
        moles.forEach(mole => {
            if (mole.visible) {
                mole.points += 1;
            }
        });
    } else if (activePowerUp.type === 'freeze') {
        moles.forEach(mole => {
            if (mole.visible) {
                mole.appearDuration *= 1.5;
            }
        });
    }
}

function drawHammer(x, y) {
    ctx.drawImage(hammerImage, x - 25, y - 25, 50, 50);
    
    setTimeout(() => {
        ctx.clearRect(x - 25, y - 25, 50, 50);
    }, 100);
}

function gameLoop(currentTime) {
    if (lastFrameTime === 0) {
        lastFrameTime = currentTime;
    }
    const deltaTime = currentTime - lastFrameTime;
    lastFrameTime = currentTime;

    ctx.clearRect(0, 0, CANVAS_WIDTH, CANVAS_HEIGHT);
    updateMoles(deltaTime);
    updatePowerUps(currentTime);
    drawMoles();
    drawPowerUps();
    applyPowerUpEffects();

    timeLeft -= deltaTime / 1000;
    timeValue.textContent = Math.ceil(timeLeft);

    if (Math.max(player1Score, player2Score) >= getDifficultySettings(getDifficultySettings().gameDuration - timeLeft).scoreToWin) {
        endGame(true);
    } else if (timeLeft <= 0) {
        endGame(false);
    } else {
        if (debugMode) {
            ctx.fillStyle = 'black';
            ctx.font = '14px Arial';
            ctx.fillText(`Game Time: ${(getDifficultySettings().gameDuration - timeLeft).toFixed(2)}s`, 10, 20);
            ctx.fillText(`FPS: ${Math.round(1000 / deltaTime)}`, 10, 40);
            if (activePowerUp) {
                ctx.fillText(`Active Power-up: ${activePowerUp.type}`, 10, 60);
            }
        }
        requestAnimationFrame(gameLoop);
    }
}

function switchPlayer() {
    currentPlayer = currentPlayer === 1 ? 2 : 1;
    document.getElementById('current-player').textContent = `Player ${currentPlayer}'s turn`;
    console.log(`Switched to Player ${currentPlayer}'s turn`);
}

function handleInteraction(event) {
    event.preventDefault();
    const rect = canvas.getBoundingClientRect();
    let x, y;

    if (event.type.startsWith('touch')) {
        const touch = event.touches[0] || event.changedTouches[0];
        x = touch.clientX - rect.left;
        y = touch.clientY - rect.top;
    } else {
        x = event.clientX - rect.left;
        y = event.clientY - rect.top;
    }

    let hitSuccessful = false;
    moles.forEach(mole => {
        const distance = Math.sqrt((x - mole.x) ** 2 + (y - mole.y) ** 2);
        if (distance < MOLE_SIZE / 2) {
            if (mole.hit()) {
                console.log(`${mole.type} Mole hit at: (${x}, ${y}), Player ${currentPlayer} Score: ${currentPlayer === 1 ? player1Score : player2Score}`);
                hitSuccessful = true;
            }
        }
    });

    if (hitSuccessful) {
        switchPlayer();
    }

    collectPowerUp(x, y);
    drawHammer(x, y);
}

function startGame() {
    fetch('/start_game', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
    })
    .then(response => {
        if (!response.ok) {
            if (response.status === 401) {
                throw new Error('User not authenticated');
            } else {
                throw new Error('Failed to start game');
            }
        }
        return response.json();
    })
    .then(data => {
        if (data.success) {
            console.log('Game started with difficulty:', selectedDifficulty);
            startScreen.style.display = 'none';
            gameScreen.style.display = 'block';
            gameOverScreen.style.display = 'none';

            player1Score = 0;
            player2Score = 0;
            currentPlayer = 1;
            const difficultySettings = getDifficultySettings(0);
            timeLeft = difficultySettings.gameDuration;
            firstMoleAppeared = false;
            lastMoleAppearance = 0;
            scoreValue.textContent = `P1: 0 | P2: 0`;
            timeValue.textContent = Math.ceil(timeLeft);
            document.getElementById('current-player').textContent = 'Player 1\'s turn';

            initializeMoles();
            lastFrameTime = 0;
            requestAnimationFrame(gameLoop);
        } else {
            throw new Error('Failed to start game');
        }
    })
    .catch((error) => {
        console.error('Error:', error);
        if (error.message === 'User not authenticated') {
            alert('Please log in to play the game.');
            window.location.href = '/login?next=' + encodeURIComponent(window.location.pathname);
        } else {
            alert('An error occurred while starting the game. Please try again.');
        }
    });
}

function endGame(isWin) {
    console.log('Game ended');
    gameScreen.style.display = 'none';
    gameOverScreen.style.display = 'block';
    
    let winner;
    if (player1Score > player2Score) {
        winner = 'Player 1';
    } else if (player2Score > player1Score) {
        winner = 'Player 2';
    } else {
        winner = 'It\'s a tie!';
    }
    
    gameResult.textContent = isWin ? `${winner} Wins!` : 'Game Over';
    finalScore.textContent = `Player 1: ${player1Score} | Player 2: ${player2Score}`;
    if (isWin) {
        winSound.play();
    } else {
        gameOverSound.play();
    }

    submitScore(Math.max(player1Score, player2Score), selectedDifficulty);
    showLeaderboard(selectedDifficulty);
}

function submitScore(score, difficulty) {
    console.log('Submitting score:', { score, difficulty });
    fetch('/submit_score', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            score: score,
            difficulty: difficulty
        }),
    })
    .then(response => {
        if (response.ok) {
            return response.json();
        } else if (response.status === 401) {
            throw new Error('User not authenticated');
        } else {
            throw new Error('Failed to submit score');
        }
    })
    .then(data => {
        console.log('Score submitted successfully:', data);
    })
    .catch((error) => {
        console.error('Error submitting score:', error);
        if (error.message === 'User not authenticated') {
            alert('Please log in to submit your score.');
        } else {
            alert('There was an error submitting your score. Please try again.');
        }
    });
}

function showLeaderboard(difficulty) {
    fetch(`/leaderboard/${difficulty}`)
    .then(response => response.json())
    .then(data => {
        console.log('Leaderboard data received:', data);
        const leaderboardHTML = `
            <h3>Leaderboard (${difficulty})</h3>
            <table>
                <tr>
                    <th>Rank</th>
                    <th>Name</th>
                    <th>Score</th>
                    <th>Date</th>
                </tr>
                ${data.map((score, index) => `
                    <tr>
                        <td>${index + 1}</td>
                        <td>${score.username}</td>
                        <td>${score.score}</td>
                        <td>${score.date}</td>
                    </tr>
                `).join('')}
            </table>
        `;
        document.getElementById('leaderboard').innerHTML = leaderboardHTML;
    })
    .catch((error) => {
        console.error('Error fetching leaderboard:', error);
        document.getElementById('leaderboard').innerHTML = '<p>Error loading leaderboard. Please try again later.</p>';
    });
}

function selectDifficulty(difficulty) {
    console.log('Difficulty selected:', difficulty);
    selectedDifficulty = difficulty;
    difficultyButtons.forEach(btn => btn.classList.remove('selected'));
    document.getElementById(`${difficulty}-button`).classList.add('selected');
    startButton.disabled = false;
}

difficultyButtons.forEach(button => {
    button.addEventListener('click', () => {
        selectDifficulty(button.id.split('-')[0]);
    });
});

canvas.addEventListener('mousedown', handleInteraction);
canvas.addEventListener('touchstart', handleInteraction);
canvas.addEventListener('touchmove', handleInteraction);
canvas.addEventListener('touchend', (event) => {
    event.preventDefault();
});

startButton.addEventListener('click', startGame);
restartButton.addEventListener('click', () => {
    startScreen.style.display = 'block';
    gameOverScreen.style.display = 'none';
    startButton.disabled = true;
    selectedDifficulty = null;
    difficultyButtons.forEach(btn => btn.classList.remove('selected'));
});

document.addEventListener('keydown', (event) => {
    if (event.key === 'd' || event.key === 'D') {
        debugMode = !debugMode;
        console.log('Debug mode:', debugMode ? 'ON' : 'OFF');
    }
});

window.onload = () => {
    console.log('Images loaded:', holeImage.complete, moleImage.complete, fastMoleImage.complete, goldenMoleImage.complete, hammerImage.complete);
};