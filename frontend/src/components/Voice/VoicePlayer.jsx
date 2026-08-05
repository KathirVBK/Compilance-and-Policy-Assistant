import React, { useState, useRef } from 'react';
import { Volume2, VolumeX, Loader2 } from 'lucide-react';
import { api } from '../../services/api';

export const VoicePlayer = ({ text }) => {
  const [isPlaying, setIsPlaying] = useState(false);
  const [loading, setLoading] = useState(false);
  const audioRef = useRef(null);

  const handlePlayToggle = async () => {
    if (isPlaying) {
      if (audioRef.current) {
        audioRef.current.pause();
        setIsPlaying(false);
      }
      return;
    }

    setLoading(true);
    try {
      const audioBlob = await api.synthesizeSpeech(text);
      const audioUrl = URL.createObjectURL(audioBlob);
      
      const audio = new Audio(audioUrl);
      audioRef.current = audio;
      
      audio.onended = () => {
        setIsPlaying(false);
      };
      
      audio.onplay = () => {
        setIsPlaying(true);
        setLoading(false);
      };

      audio.onerror = () => {
        setIsPlaying(false);
        setLoading(false);
        alert("Audio playback failed.");
      };

      await audio.play();
    } catch (err) {
      console.error("TTS error:", err);
      setLoading(false);
      alert("Text-to-speech synthesis failed.");
    }
  };

  return (
    <button 
      className={`voice-player-btn ${isPlaying ? 'playing' : ''}`}
      onClick={handlePlayToggle}
      disabled={loading}
      title={isPlaying ? "Mute audio" : "Listen to answer"}
    >
      {loading ? (
        <Loader2 className="spinning" size={14} />
      ) : isPlaying ? (
        <VolumeX size={14} />
      ) : (
        <Volume2 size={14} />
      )}
    </button>
  );
};
export default VoicePlayer;
