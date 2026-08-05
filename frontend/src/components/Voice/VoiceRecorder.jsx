import React, { useState, useRef } from 'react';
import { Mic, Square } from 'lucide-react';
import { api } from '../../services/api';

export const VoiceRecorder = ({ onTranscriptionComplete }) => {
  const [isRecording, setIsRecording] = useState(false);
  const [loading, setLoading] = useState(false);
  const mediaRecorderRef = useRef(null);
  const chunksRef = useRef([]);

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      mediaRecorderRef.current = new MediaRecorder(stream, { mimeType: 'audio/webm' });
      chunksRef.current = [];

      mediaRecorderRef.current.ondataavailable = (e) => {
        if (e.data && e.data.size > 0) {
          chunksRef.current.push(e.data);
        }
      };

      mediaRecorderRef.current.onstop = async () => {
        const audioBlob = new Blob(chunksRef.current, { type: 'audio/webm' });
        stream.getTracks().forEach(track => track.stop()); // close microphone stream
        
        setLoading(true);
        try {
          const res = await api.transcribeSpeech(audioBlob);
          if (res.text) {
            onTranscriptionComplete(res.text);
          }
        } catch (err) {
          console.error("Transcription error:", err);
          alert("Audio transcription failed. Using keyboard backup.");
        } finally {
          setLoading(false);
        }
      };

      mediaRecorderRef.current.start();
      setIsRecording(true);
    } catch (err) {
      console.error("Microphone access blocked:", err);
      alert("Microphone access was blocked. Please check your browser permissions.");
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
    }
  };

  return (
    <div className="voice-recorder-container">
      {isRecording && (
        <div className="voice-wave-overlay">
          <div className="wave-bar"></div>
          <div className="wave-bar"></div>
          <div className="wave-bar"></div>
          <div className="wave-bar"></div>
          <span className="wave-lbl">Listening...</span>
        </div>
      )}
      
      <button 
        type="button" 
        className={`voice-mic-btn ${isRecording ? 'recording' : ''}`}
        onClick={isRecording ? stopRecording : startRecording}
        disabled={loading}
        title={isRecording ? "Stop recording" : "Speak your query"}
      >
        {isRecording ? <Square size={16} /> : <Mic size={16} />}
      </button>
    </div>
  );
};
export default VoiceRecorder;
