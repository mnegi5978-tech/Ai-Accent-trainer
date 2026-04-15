const difficultySelect = document.getElementById("difficultySelect");
const sentenceSelect = document.getElementById("sentenceSelect");
const sentenceInput = document.getElementById("sentenceInput");
const startBtn = document.getElementById("startBtn");
const recordState = document.getElementById("recordState");
const accuracyValue = document.getElementById("accuracyValue");
const transcriptText = document.getElementById("transcriptText");
const mistakeText = document.getElementById("mistakeText");
const tipText = document.getElementById("tipText");
const analysisHtml = document.getElementById("analysisHtml");
const replayBtn = document.getElementById("replayBtn");

let audioContext;
let processor;
let stream;
let audioData = [];
let mediaStreamSource;
let isRecording = false;
let currentAudioUrl = null;

function updateSentenceOptions() {
  const difficulty = difficultySelect.value;
  const sentences = practiceData[difficulty] || [];
  sentenceSelect.innerHTML = "";
  sentences.forEach((sentence) => {
    const option = document.createElement("option");
    option.value = sentence;
    option.textContent = sentence;
    sentenceSelect.appendChild(option);
  });
  if (sentences.length > 0) {
    sentenceSelect.selectedIndex = 0;
    sentenceInput.value = sentences[0];
  }
}

function setRecordState(message) {
  recordState.textContent = message;
}

function toggleRecording() {
  if (isRecording) {
    stopRecording();
  } else {
    startRecording();
  }
}

async function startRecording() {
  if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
    alert("Your browser does not support microphone recording.");
    return;
  }

  try {
    stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    audioContext = new (window.AudioContext || window.webkitAudioContext)();
    mediaStreamSource = audioContext.createMediaStreamSource(stream);
    processor = audioContext.createScriptProcessor(4096, 1, 1);

    processor.onaudioprocess = (event) => {
      const buffer = event.inputBuffer.getChannelData(0);
      audioData.push(new Float32Array(buffer));
    };

    mediaStreamSource.connect(processor);
    processor.connect(audioContext.destination);
    isRecording = true;
    startBtn.textContent = "Stop Recording";
    startBtn.classList.add("active");
    setRecordState("Recording... speak clearly into your microphone.");
  } catch (error) {
    console.error(error);
    alert("Unable to access the microphone. Please allow microphone access.");
  }
}

function stopRecording() {
  if (!isRecording) {
    return;
  }

  isRecording = false;
  startBtn.textContent = "🎤 Start Speaking";
  startBtn.classList.remove("active");
  setRecordState("Processing audio...");

  processor.disconnect();
  mediaStreamSource.disconnect();
  stream.getTracks().forEach((track) => track.stop());

  const wavBlob = encodeWAV(mergeBuffers(audioData), audioContext.sampleRate);
  audioData = [];
  analyzeAudio(wavBlob);
}

function mergeBuffers(channelBuffer) {
  let length = 0;
  channelBuffer.forEach((buffer) => {
    length += buffer.length;
  });
  const result = new Float32Array(length);
  let offset = 0;
  channelBuffer.forEach((buffer) => {
    result.set(buffer, offset);
    offset += buffer.length;
  });
  return result;
}

function encodeWAV(samples, sampleRate) {
  const buffer = new ArrayBuffer(44 + samples.length * 2);
  const view = new DataView(buffer);

  function writeString(offset, string) {
    for (let i = 0; i < string.length; i++) {
      view.setUint8(offset + i, string.charCodeAt(i));
    }
  }

  function floatTo16BitPCM(output, offset, input) {
    for (let i = 0; i < input.length; i++, offset += 2) {
      let s = Math.max(-1, Math.min(1, input[i]));
      view.setInt16(offset, s < 0 ? s * 0x8000 : s * 0x7fff, true);
    }
  }

  writeString(0, "RIFF");
  view.setUint32(4, 36 + samples.length * 2, true);
  writeString(8, "WAVE");
  writeString(12, "fmt ");
  view.setUint32(16, 16, true);
  view.setUint16(20, 1, true);
  view.setUint16(22, 1, true);
  view.setUint32(24, sampleRate, true);
  view.setUint32(28, sampleRate * 2, true);
  view.setUint16(32, 2, true);
  view.setUint16(34, 16, true);
  writeString(36, "data");
  view.setUint32(40, samples.length * 2, true);
  floatTo16BitPCM(view, 44, samples);

  return new Blob([view], { type: "audio/wav" });
}

function blobToDataURL(blob) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onloadend = () => resolve(reader.result);
    reader.onerror = reject;
    reader.readAsDataURL(blob);
  });
}

async function analyzeAudio(blob) {
  try {
    const audioBase64 = await blobToDataURL(blob);
    const recordResponse = await fetch("/record", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ audioBase64 }),
    });
    const recordResult = await recordResponse.json();

    if (!recordResult.success) {
      setRecordState("Could not transcribe audio. Try again.");
      return;
    }

    const payload = {
      sentence: sentenceInput.value.trim(),
      transcript: recordResult.transcript,
      difficulty: difficultySelect.value,
    };

    const analysisResponse = await fetch("/analyze", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    const analysisResult = await analysisResponse.json();
    if (!analysisResult.success) {
      throw new Error(analysisResult.message || "Analysis failed");
    }

    updateResultUI(analysisResult);
    setRecordState("Analysis complete.");
  } catch (error) {
    console.error(error);
    setRecordState("Recording failed. Please try again.");
  }
}

function updateResultUI(result) {
  accuracyValue.textContent = `${result.accuracy}%`;
  transcriptText.textContent = result.transcript || "(Could not understand spoken words)";
  mistakeText.textContent = result.wrong_words.length
    ? result.wrong_words.join(", ")
    : "All words sound good. Great job!";
  tipText.textContent = result.pronunciation_tip;
  analysisHtml.innerHTML = result.colored_html || "<p class='hint'>No sentence analysis available.</p>";

  if (result.audio_url) {
    currentAudioUrl = result.audio_url;
    replayBtn.disabled = false;
  } else {
    replayBtn.disabled = true;
  }
}

replayBtn.addEventListener("click", () => {
  if (!currentAudioUrl) {
    return;
  }
  const audio = new Audio(currentAudioUrl);
  audio.play();
});

difficultySelect.addEventListener("change", updateSentenceOptions);
sentenceSelect.addEventListener("change", () => {
  sentenceInput.value = sentenceSelect.value;
});

startBtn.addEventListener("click", toggleRecording);

updateSentenceOptions();
