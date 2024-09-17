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

const CANVAS_WIDTH = 600;
const CANVAS_HEIGHT = 400;
const GRID_SIZE = 3;
const HOLE_SIZE = 100;
const MOLE_SIZE = 80;
const GAME_DURATION = 45;

canvas.width = CANVAS_WIDTH;
canvas.height = CANVAS_HEIGHT;

let score = 0;
let timeLeft = GAME_DURATION;
let gameInterval;
let moles = [];
let debugMode = false;
let lastFrameTime = 0;
let firstMoleAppeared = false;
let lastMoleAppearance = 0;

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

let whackSound, moleAppearSound, gameOverSound;

Promise.all([
    loadAudio('/static/assets/whack.mp3'),
    loadAudio('/static/assets/mole_appear.mp3'),
    loadAudio('/static/assets/game_over.mp3')
]).then(([whack, moleAppear, gameOver]) => {
    whackSound = whack;
    moleAppearSound = moleAppear;
    gameOverSound = gameOver;
    console.log('All audio files loaded successfully');
}).catch(error => {
    console.error('Error loading audio files:', error);
    // Disable audio functionality if files fail to load
    whackSound = moleAppearSound = gameOverSound = { play: () => {} };
});

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
            score += this.points;
            scoreValue.textContent = score;
            whackSound.play();
            return true;
        }
        return false;
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

function updateMoles(deltaTime) {
    const now = Date.now();
    const gameTime = GAME_DURATION - timeLeft;
    let maxVisibleMoles, maxAppearDuration;

    // Determine the current game phase
    if (gameTime <= 7) {
        maxVisibleMoles = 1;
        maxAppearDuration = 2000;
    } else if (gameTime <= 16) {
        maxVisibleMoles = 2;
        maxAppearDuration = 1520;
    } else {
        maxVisibleMoles = 1;
        maxAppearDuration = 920;
    }

    const visibleMoles = moles.filter(mole => mole.visible).length;

    // Spawn new moles if there are fewer visible moles than the maximum allowed
    if (visibleMoles < maxVisibleMoles) {
        const availableMoles = moles.filter(mole => !mole.visible);
        if (availableMoles.length > 0) {
            const spawnChance = maxVisibleMoles - visibleMoles; // Higher chance to spawn when fewer moles are visible
            if (Math.random() < spawnChance * 0.5) { // Adjust this multiplier to control spawn frequency
                const randomMole = availableMoles[Math.floor(Math.random() * availableMoles.length)];
                randomMole.visible = true;
                randomMole.lastAppearance = now;

                // Determine mole type based on probabilities
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

    // Update existing moles
    moles.forEach(mole => {
        if (mole.visible && now - mole.lastAppearance > mole.appearDuration) {
            mole.visible = false;
            console.log(`${mole.type} Mole disappeared at: (${mole.x}, ${mole.y}), Time: ${now}, Duration: ${now - mole.lastAppearance}ms`);
        }
    });

    console.log(`Moles updated, visible moles: ${visibleMoles}, Game Time: ${gameTime.toFixed(2)}s, Max Visible: ${maxVisibleMoles}, Max Appear Duration: ${maxAppearDuration}ms`);
}

function drawHammer(x, y) {
    ctx.drawImage(hammerImage, x - 25, y - 25, 50, 50);
}

function gameLoop(currentTime) {
    if (lastFrameTime === 0) {
        lastFrameTime = currentTime;
    }
    const deltaTime = currentTime - lastFrameTime;
    lastFrameTime = currentTime;

    ctx.clearRect(0, 0, CANVAS_WIDTH, CANVAS_HEIGHT);
    updateMoles(deltaTime);
    drawMoles();

    timeLeft -= deltaTime / 1000;
    timeValue.textContent = Math.ceil(timeLeft);

    if (timeLeft <= 0) {
        endGame();
    } else {
        if (debugMode) {
            ctx.fillStyle = 'black';
            ctx.font = '14px Arial';
            ctx.fillText(`Game Time: ${(GAME_DURATION - timeLeft).toFixed(2)}s`, 10, 20);
            ctx.fillText(`FPS: ${Math.round(1000 / deltaTime)}`, 10, 40);
        }
        requestAnimationFrame(gameLoop);
    }
}

function startGame() {
    console.log('Game started');
    startScreen.style.display = 'none';
    gameScreen.style.display = 'block';
    gameOverScreen.style.display = 'none';

    score = 0;
    timeLeft = GAME_DURATION;
    firstMoleAppeared = false;
    lastMoleAppearance = 0;
    scoreValue.textContent = score;
    timeValue.textContent = Math.ceil(timeLeft);

    initializeMoles();
    lastFrameTime = 0;
    requestAnimationFrame(gameLoop);
}

function endGame() {
    console.log('Game ended');
    gameScreen.style.display = 'none';
    gameOverScreen.style.display = 'block';
    finalScore.textContent = score;
    gameOverSound.play();
}

canvas.addEventListener('click', (event) => {
    const rect = canvas.getBoundingClientRect();
    const x = event.clientX - rect.left;
    const y = event.clientY - rect.top;

    moles.forEach(mole => {
        const distance = Math.sqrt((x - mole.x) ** 2 + (y - mole.y) ** 2);
        if (distance < MOLE_SIZE / 2) {
            if (mole.hit()) {
                console.log(`${mole.type} Mole hit at: (${x}, ${y}), Score: ${score}`);
            }
        }
    });

    drawHammer(x, y);
});

startButton.addEventListener('click', startGame);
restartButton.addEventListener('click', startGame);

// Toggle debug mode
document.addEventListener('keydown', (event) => {
    if (event.key === 'd' || event.key === 'D') {
        debugMode = !debugMode;
        console.log('Debug mode:', debugMode ? 'ON' : 'OFF');
    }
});

// Preload images
window.onload = () => {
    console.log('Images loaded:', holeImage.complete, moleImage.complete, fastMoleImage.complete, goldenMoleImage.complete, hammerImage.complete);
};
