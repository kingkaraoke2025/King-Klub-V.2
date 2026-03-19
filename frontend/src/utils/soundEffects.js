// Sound effects utility for King Klub
// Uses Web Audio API to generate sounds

class SoundEffects {
  constructor() {
    this.audioContext = null;
    this.enabled = true;
  }

  init() {
    if (!this.audioContext) {
      this.audioContext = new (window.AudioContext || window.webkitAudioContext)();
    }
    return this.audioContext;
  }

  setEnabled(enabled) {
    this.enabled = enabled;
  }

  // Play a royal fanfare for battle voting opening
  playBattleStart() {
    if (!this.enabled) return;
    const ctx = this.init();
    
    // Create a majestic fanfare sound
    const notes = [
      { freq: 523.25, start: 0, duration: 0.15 },     // C5
      { freq: 659.25, start: 0.15, duration: 0.15 },  // E5
      { freq: 783.99, start: 0.3, duration: 0.15 },   // G5
      { freq: 1046.50, start: 0.45, duration: 0.4 },  // C6 (hold)
    ];

    notes.forEach(note => {
      const oscillator = ctx.createOscillator();
      const gainNode = ctx.createGain();
      
      oscillator.connect(gainNode);
      gainNode.connect(ctx.destination);
      
      oscillator.type = 'triangle';
      oscillator.frequency.value = note.freq;
      
      const startTime = ctx.currentTime + note.start;
      gainNode.gain.setValueAtTime(0.3, startTime);
      gainNode.gain.exponentialRampToValueAtTime(0.01, startTime + note.duration);
      
      oscillator.start(startTime);
      oscillator.stop(startTime + note.duration);
    });
  }

  // Play a vote confirmation sound
  playVoteConfirm() {
    if (!this.enabled) return;
    const ctx = this.init();
    
    const oscillator = ctx.createOscillator();
    const gainNode = ctx.createGain();
    
    oscillator.connect(gainNode);
    gainNode.connect(ctx.destination);
    
    oscillator.type = 'sine';
    oscillator.frequency.setValueAtTime(880, ctx.currentTime);
    oscillator.frequency.exponentialRampToValueAtTime(1320, ctx.currentTime + 0.1);
    
    gainNode.gain.setValueAtTime(0.2, ctx.currentTime);
    gainNode.gain.exponentialRampToValueAtTime(0.01, ctx.currentTime + 0.2);
    
    oscillator.start(ctx.currentTime);
    oscillator.stop(ctx.currentTime + 0.2);
  }

  // Play a warning tick for low time
  playTimerTick() {
    if (!this.enabled) return;
    const ctx = this.init();
    
    const oscillator = ctx.createOscillator();
    const gainNode = ctx.createGain();
    
    oscillator.connect(gainNode);
    gainNode.connect(ctx.destination);
    
    oscillator.type = 'square';
    oscillator.frequency.value = 800;
    
    gainNode.gain.setValueAtTime(0.1, ctx.currentTime);
    gainNode.gain.exponentialRampToValueAtTime(0.01, ctx.currentTime + 0.05);
    
    oscillator.start(ctx.currentTime);
    oscillator.stop(ctx.currentTime + 0.05);
  }

  // Play urgent warning sound for last 10 seconds
  playUrgentWarning() {
    if (!this.enabled) return;
    const ctx = this.init();
    
    [0, 0.15].forEach((delay, i) => {
      const oscillator = ctx.createOscillator();
      const gainNode = ctx.createGain();
      
      oscillator.connect(gainNode);
      gainNode.connect(ctx.destination);
      
      oscillator.type = 'sawtooth';
      oscillator.frequency.value = i === 0 ? 600 : 800;
      
      const startTime = ctx.currentTime + delay;
      gainNode.gain.setValueAtTime(0.15, startTime);
      gainNode.gain.exponentialRampToValueAtTime(0.01, startTime + 0.1);
      
      oscillator.start(startTime);
      oscillator.stop(startTime + 0.1);
    });
  }

  // Play victory fanfare
  playVictory() {
    if (!this.enabled) return;
    const ctx = this.init();
    
    const notes = [
      { freq: 523.25, start: 0, duration: 0.12 },
      { freq: 659.25, start: 0.12, duration: 0.12 },
      { freq: 783.99, start: 0.24, duration: 0.12 },
      { freq: 1046.50, start: 0.36, duration: 0.12 },
      { freq: 1318.51, start: 0.48, duration: 0.5 },
    ];

    notes.forEach(note => {
      const oscillator = ctx.createOscillator();
      const gainNode = ctx.createGain();
      
      oscillator.connect(gainNode);
      gainNode.connect(ctx.destination);
      
      oscillator.type = 'triangle';
      oscillator.frequency.value = note.freq;
      
      const startTime = ctx.currentTime + note.start;
      gainNode.gain.setValueAtTime(0.25, startTime);
      gainNode.gain.exponentialRampToValueAtTime(0.01, startTime + note.duration);
      
      oscillator.start(startTime);
      oscillator.stop(startTime + note.duration);
    });
  }

  // Play voting closed sound
  playVotingClosed() {
    if (!this.enabled) return;
    const ctx = this.init();
    
    const oscillator = ctx.createOscillator();
    const gainNode = ctx.createGain();
    
    oscillator.connect(gainNode);
    gainNode.connect(ctx.destination);
    
    oscillator.type = 'sine';
    oscillator.frequency.setValueAtTime(880, ctx.currentTime);
    oscillator.frequency.exponentialRampToValueAtTime(440, ctx.currentTime + 0.3);
    
    gainNode.gain.setValueAtTime(0.2, ctx.currentTime);
    gainNode.gain.exponentialRampToValueAtTime(0.01, ctx.currentTime + 0.3);
    
    oscillator.start(ctx.currentTime);
    oscillator.stop(ctx.currentTime + 0.3);
  }

  // Play challenge received sound - dramatic alert
  playChallengeReceived() {
    if (!this.enabled) return;
    const ctx = this.init();
    
    // Dramatic "sword clash" sound
    const notes = [
      { freq: 220, start: 0, duration: 0.1, type: 'sawtooth' },
      { freq: 440, start: 0.05, duration: 0.15, type: 'square' },
      { freq: 880, start: 0.15, duration: 0.2, type: 'triangle' },
      { freq: 660, start: 0.3, duration: 0.3, type: 'sine' },
    ];

    notes.forEach(note => {
      const oscillator = ctx.createOscillator();
      const gainNode = ctx.createGain();
      
      oscillator.connect(gainNode);
      gainNode.connect(ctx.destination);
      
      oscillator.type = note.type;
      oscillator.frequency.value = note.freq;
      
      const startTime = ctx.currentTime + note.start;
      gainNode.gain.setValueAtTime(0.25, startTime);
      gainNode.gain.exponentialRampToValueAtTime(0.01, startTime + note.duration);
      
      oscillator.start(startTime);
      oscillator.stop(startTime + note.duration);
    });
  }

  // Play challenge accepted sound - triumphant confirmation
  playChallengeAccepted() {
    if (!this.enabled) return;
    const ctx = this.init();
    
    // Rising triumphant sound
    const notes = [
      { freq: 392, start: 0, duration: 0.15 },      // G4
      { freq: 523.25, start: 0.12, duration: 0.15 }, // C5
      { freq: 659.25, start: 0.24, duration: 0.15 }, // E5
      { freq: 783.99, start: 0.36, duration: 0.35 }, // G5 (hold)
    ];

    notes.forEach(note => {
      const oscillator = ctx.createOscillator();
      const gainNode = ctx.createGain();
      
      oscillator.connect(gainNode);
      gainNode.connect(ctx.destination);
      
      oscillator.type = 'triangle';
      oscillator.frequency.value = note.freq;
      
      const startTime = ctx.currentTime + note.start;
      gainNode.gain.setValueAtTime(0.3, startTime);
      gainNode.gain.exponentialRampToValueAtTime(0.01, startTime + note.duration);
      
      oscillator.start(startTime);
      oscillator.stop(startTime + note.duration);
    });
  }

  // Play admin notification sound - attention grabber
  playAdminAlert() {
    if (!this.enabled) return;
    const ctx = this.init();
    
    // Double beep alert
    [0, 0.2].forEach((delay) => {
      const oscillator = ctx.createOscillator();
      const gainNode = ctx.createGain();
      
      oscillator.connect(gainNode);
      gainNode.connect(ctx.destination);
      
      oscillator.type = 'sine';
      oscillator.frequency.value = 1000;
      
      const startTime = ctx.currentTime + delay;
      gainNode.gain.setValueAtTime(0.25, startTime);
      gainNode.gain.exponentialRampToValueAtTime(0.01, startTime + 0.12);
      
      oscillator.start(startTime);
      oscillator.stop(startTime + 0.12);
    });
  }
}

// Export singleton instance
const soundEffects = new SoundEffects();
export default soundEffects;
