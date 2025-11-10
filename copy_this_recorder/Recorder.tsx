import React, { useEffect, useState, useRef } from "react";
import {
  useAudioRecorder,
  AudioModule,
  useAudioRecorderState,
  setAudioModeAsync,
  RecordingPresets,
  RecordingStatus,
  AudioRecorder,
  useAudioPlayer,
} from "expo-audio";
import { Audio } from "expo-av";
import {
  Button,
  StyleSheet,
  Text,
  TouchableOpacity,
  TextInput,
  View,
  Image,
  Alert,
  Platform,
  KeyboardAvoidingView,
  ActivityIndicator,
} from "react-native";
import YoutubePlayer from "react-native-youtube-iframe";
import { SafeAreaView, SafeAreaProvider } from "react-native-safe-area-context";

function extractYouTubeVideoId(url: string | null): string {
  if (!url) return "";
  const match = url.match(
    /(?:youtube\.com\/.*v=|youtu\.be\/)([a-zA-Z0-9_-]{11})/
  );
  return match ? match[1] : url;
}

export default function Recorder() {
  const [audioInput, setAudioInput] = useState("device");
  const [uri, setUri] = useState<any>(null);
  const [text, setText] = React.useState("");
  const audioRecorder = useAudioRecorder({
    extension: ".m4a",
    numberOfChannels: 2,
    sampleRate: 44100,
    bitRate: 128000,
    android: {
      extension: ".wav",
      outputFormat: "mpeg4",
      audioEncoder: "aac",
      sampleRate: 44100,
    },
    ios: {
      extension: ".wav",
      audioQuality: 2,
      sampleRate: 44100,
      linearPCMBitDepth: 16,
      linearPCMIsBigEndian: false,
      linearPCMIsFloat: false,
    },
    web: {
      mimeType: "audio/wav",
    },
  });
  const recorderState = useAudioRecorderState(audioRecorder);
  const [predictedSong, setPredictedSong] = useState<string | null>(null);
  const [predictedConfidence, setPredictedConfidence] = useState<number | null>(
    null
  );
  const [predictedUrl, setPredictedUrl] = useState<string | null>(null);
  const [showPrediction, setShowPrediction] = useState(false);
  const [addingSong, setAddingSong] = useState(false);
  // const audioPlayer = useAudioPlayer();
  // const [audioPlayer, setAudioPlayer] = useState(null);
  //   const [permission, requestPermission] = useAudPermissions();

  const record = async () => {
    await audioRecorder.prepareToRecordAsync();
    audioRecorder.record();
  };

  const stopRecording = async () => {
    await audioRecorder.stop();
    setUri(audioRecorder.uri);
  };

  useEffect(() => {
    (async () => {
      const status = await AudioModule.getRecordingPermissionsAsync();
      if (!status.granted) {
        Alert.alert(
          "Permission to access microphone must be given to use the app"
        );
      }

      setAudioModeAsync({
        playsInSilentMode: true,
        allowsRecording: true,
      });
    })();
  }, []);

  const handlePrediction = async () => {
    console.log("Handling prediction...");
    if (uri) {
      // const response = await getPredictedSong();

      const formData = new FormData();

      // Lets encode the URI of our recording to a blob
      const responsee = await fetch(uri);
      //const blob = await responsee.blob();

      // Create a file from the blob
      //const file = new File([blob], "audio.flac", { type: "audio/flac" });

      //console.log("Audio file being sent:", file);

      // Append the actual file to FormData
      formData.append("audio", {
        uri: uri,
        type: "audio/flac",
        name: "audio.flac"
      } as any);

      console.log("Sending POST request to server...");

      // TODO: type in your server address here
      const predict_endpoint = "http://35.3.232.66:5003/predict";

      // This is our first JavaScript promise which is a fetch request to the server
      // We start by making a post request to our prediction endpoint using the form data above
      // which contains our audio file
      fetch(predict_endpoint, {
        method: "POST",
        body: formData,
      })
        .then((response) => {
          // If we are at this point, our promise has been fulfilled and we have a response form the server!
          // We convert the response to JSON to make it easier to work with in JavaScript
          return response.json();
        })
        .then((data) => {
          // Now that we have the JSON data, we can change our state to reflect the prediction
          // TODO: Change important varaibles now that we have our prediction data
          // Hint: Some variables we might want to change are saving the predicted song,
          // the url of the associated youtube video, and some marker so our app knows to show the prediction
          setPredictedSong(data.song);
          setPredictedConfidence(data.confidence);
          setPredictedUrl(data.youtube_url);
          setShowPrediction(true);
        })
        .catch((error) => {
          console.error("Error in prediction fetch:", error);
        });
    }
  };

  async function addSongToDatabase(song_url: any) {
    console.log("Adding song to database:", song_url);

    setAddingSong(true);

    const formData = new FormData();

    // TODO: Append the correct data to our form in a way that our endpoint can access
    formData.append("youtube_url", song_url);

    // TODO: type in your server address here
    const add_endpoint = "http://35.3.232.66:5003/add";

    // TODO: follow handlePrediction's fetch structure to make a JavaScript fetch
    fetch(add_endpoint, {
      method: "POST",
      body: formData,
    })
      .then((response) => {
        return response.json();
      })
      .catch((error) => {
        console.error("Error in prediction fetch:", error);
      });
  }

  return (
    <>
      <SafeAreaProvider>
        <SafeAreaView style={styles.container}>
          <View style={{ width: 150, marginBottom: 20, marginTop: 50 }}>
            {/** This is our button to start/stop recording. Depending on the state it will
             * trigger the stopRecording or record function. **/}
            <TouchableOpacity
              style={styles.recorderButton}
              onPress={recorderState.isRecording ? stopRecording : record}
            >
              {recorderState.isRecording ? (
                <Image
                  source={require("../../assets/images/square-icon.png")}
                  style={{ width: 100, height: 100 }}
                />
              ) : (
                <Image
                  source={require("../../assets/images/microphone-icon.png")}
                  style={{ width: 100, height: 100 }}
                />
              )}
            </TouchableOpacity>
          </View>

          {/** Use this button to test if you are recording audio correctly. **/}
          <View style={{ width: 150, marginBottom: 20, marginTop: 20 }}>
            {/** onPress creates a new sound object and plays the recorded audio. **/}
            <Button
              title="Play Recording"
              onPress={async () => {
                // console.log("Loading sound..");
                const { sound } = await Audio.Sound.createAsync(
                  { uri: uri },
                  { shouldPlay: true }
                );

                // console.log("Playing sound..");
                await sound.playAsync();
              }}
            />
          </View>

          {/** This is our button to make a prediction. Notice how once we press it
           * and event triggering the handlePrediction function occurs. **/}
          <View style={{ width: 150, marginBottom: 10, marginTop: 20 }}>
            <Button title="Predict Song" onPress={handlePrediction} />
          </View>

          {/** If predictSong is True (i.e. we have a prediction made) then lets show
           * the prediction details. **/}
          {predictedSong && (
            <View style={{ alignItems: "center", marginTop: 20 }}>
              <Text style={{ fontSize: 15, marginBottom: 20 }}>
                Here is the most likely song from the recorded snippet!
              </Text>

              <YoutubePlayer
                height={180}
                scale={4}
                play={false}
                videoId={extractYouTubeVideoId(predictedUrl)}
                style={{ alignSelf: "stretch", marginTop: 20 }}
              />
              <Text>If this does not look correct:</Text>
              <Text>1: Please try again with a new clip.</Text>
              <Text>2: Add the song to our database below.</Text>
            </View>
          )}

          {/** KeyboardAvoidingView should make it so on an iOS device the keyboard does not cover the input field. **/}
          <KeyboardAvoidingView
            behavior={Platform.OS === "ios" ? "padding" : "height"} // "padding" works best on iOS
            keyboardVerticalOffset={0} // adjust if you have headers/navbars
          >
            {/** This is our input field for typing in a YouTube URL we want to add to the database. **/}

            {/** TODO: If we press enter on this form, we want to trigger adding our text to the database.
             * Finish implementing the onSubmitEditing function so that it triggers our javascript function
             * for adding a song to the database. **/}
            <TextInput
              style={{
                width: "100%",
                alignSelf: "center",
                marginBottom: 10,
                marginTop: 20,
                backgroundColor: "#e0e0e0",
                padding: 10,
                borderRadius: 5,
              }}
              value={text}
              onChangeText={setText}
              placeholder="Enter YouTube URL here..."
              onSubmitEditing={() => addSongToDatabase(text)}
              returnKeyType="done"
            />
          </KeyboardAvoidingView>

          {/** This is our loading indicator that shows up when we are adding a song to the database. **/}
          {addingSong && (
            <View style={{ width: 150, marginBottom: 20, marginTop: 10 }}>
              <ActivityIndicator size="small" color="#0000ff" />
            </View>
          )}

          {/** This is our button to add a song to the database. It only shows up if we are not currently adding a song. **/}
          {!addingSong && (
            <View style={{ width: 150, marginBottom: 20, marginTop: 10 }}>
              {/** Implement the same function as above for onPress to add a song to the database. **/}
              <Button title="Add Song" onPress={() => addSongToDatabase(text)} />
            </View>
          )}
        </SafeAreaView>
      </SafeAreaProvider>
    </>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    alignItems: "center",
    justifyContent: "center",
    marginHorizontal: 20,
    backgroundColor: "#ffffffea",
  },
  button: {
    backgroundColor: "#539eb2ff",
    padding: 15,
    borderRadius: 10,
    marginVertical: 10,
  },
  recorderButton: {
    backgroundColor: "#539eb2ff",
    padding: 15,
    width: 150,
    height: 150,
    borderRadius: 100,
    marginVertical: 10,
    alignItems: "center",
    justifyContent: "center",
  },
});