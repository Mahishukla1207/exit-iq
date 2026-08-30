// Web Speech API Voice Synthesizer for Emergency EOC Announcements

let isMuted = false;

export const setAudioMuted = (muted) => {
  isMuted = muted;
  if (muted && 'speechSynthesis' in window) {
    window.speechSynthesis.cancel();
  }
};

export const isAudioMuted = () => isMuted;

export const speakEmergencyAlert = (text) => {
  if (isMuted || !('speechSynthesis' in window)) return;

  try {
    window.speechSynthesis.cancel(); // Cancel ongoing speech
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.rate = 1.05; // Slightly faster for tactical urgency
    utterance.pitch = 1.0;
    utterance.volume = 1.0;
    
    // Select English voice if available
    const voices = window.speechSynthesis.getVoices();
    const engVoice = voices.find(v => v.lang.startsWith('en'));
    if (engVoice) utterance.voice = engVoice;

    window.speechSynthesis.speak(utterance);
  } catch (err) {
    console.warn('Speech synthesis failed:', err);
  }
};
