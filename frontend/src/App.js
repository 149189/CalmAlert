import React, { useState, useEffect, useRef, useCallback } from "react";
import { ThemeProvider, createTheme } from "@mui/material/styles";
import CssBaseline from "@mui/material/CssBaseline";
import {
  Box,
  Button,
  Card,
  CardContent,
  Grid,
  Paper,
  Typography,
  IconButton,
  Snackbar,
  Alert,
  Stack,
} from "@mui/material";
import {
  Mic,
  MicOff,
  Warning,
  Settings,
  NotificationsActive,
} from "@mui/icons-material";

// Theme configuration
const theme = createTheme({
  palette: {
    mode: "dark",
    primary: { main: "#00e676" },
    secondary: { main: "#ff3d00" },
    background: { default: "#121212", paper: "#1e1e1e" },
  },
  typography: { fontFamily: "Roboto, Arial" },
});

function App() {
  const [isMonitoring, setIsMonitoring] = useState(false);
  const [alerts, setAlerts] = useState([]);
  const [connectionStatus, setConnectionStatus] = useState("disconnected");
  const [systemStatus, setSystemStatus] = useState({
    wakewordModel: false,
    panicModel: false,
    audioInput: false,
  });

  const ws = useRef(null);
  const audioContext = useRef(null);
  const mediaStream = useRef(null);
  const canvasRef = useRef(null);

  // WebSocket connection
  useEffect(() => {
    if (isMonitoring) {
      connectWebSocket();
      return () => {
        if (ws.current) {
          ws.current.close();
        }
        cleanupAudio();
      };
    }
  }, [isMonitoring, connectWebSocket]);

  const connectWebSocket = useCallback(() => {
    setConnectionStatus("connecting");
    ws.current = new WebSocket("ws://localhost:8000/ws/monitoring/");

    ws.current.onopen = () => {
      setConnectionStatus("connected");
      startAudioCapture();
    };

    ws.current.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        handleIncomingAlert(data);
      } catch (error) {
        console.error("Error parsing incoming message:", error);
      }
    };

    ws.current.onerror = (error) => {
      console.error("WebSocket error:", error);
      setConnectionStatus("disconnected");
    };
  }, []);

  // Cleanup audio resources
  const cleanupAudio = () => {
    if (mediaStream.current) {
      mediaStream.current.getTracks().forEach((track) => track.stop());
      mediaStream.current = null;
    }
    if (audioContext.current) {
      audioContext.current.close();
      audioContext.current = null;
    }
  };

  // Audio processing
  const startAudioCapture = useCallback(async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      mediaStream.current = stream;
      audioContext.current = new AudioContext({ sampleRate: 16000 });
      const source = audioContext.current.createMediaStreamSource(stream);

      // Using a ScriptProcessor is deprecated; however, for simplicity we retain it here.
      const processor = audioContext.current.createScriptProcessor(4096, 1, 1);
      source.connect(processor);
      processor.connect(audioContext.current.destination);

      processor.onaudioprocess = (e) => {
        const audioData = e.inputBuffer.getChannelData(0);
        visualizeWaveform(audioData);
        if (ws.current && ws.current.readyState === WebSocket.OPEN) {
          // Convert normalized float32 [-1, 1] to int16 and send as binary data.
          const int16Data = Int16Array.from(
            audioData.map((n) => Math.max(-1, Math.min(1, n)) * 32767)
          );
          ws.current.send(int16Data.buffer);
        }
      };

      setSystemStatus((prev) => ({ ...prev, audioInput: true }));
    } catch (error) {
      console.error("Audio capture error:", error);
      addAlert("error", "Microphone access denied");
    }
  }, []);

  // Visualization
  const visualizeWaveform = useCallback((data) => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const { width, height } = canvas;
    ctx.fillStyle = theme.palette.background.paper;
    ctx.fillRect(0, 0, width, height);
    ctx.lineWidth = 2;
    ctx.strokeStyle = theme.palette.primary.main;
    ctx.beginPath();

    const sliceWidth = width / data.length;
    let x = 0;
    for (let i = 0; i < data.length; i++) {
      const y = (data[i] * height) / 2 + height / 2;
      i === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y);
      x += sliceWidth;
    }
    ctx.stroke();
  }, []);

  // Alert handling
  const handleIncomingAlert = useCallback((data) => {
    if (data.type === "panic") {
      addAlert(
        "panic",
        `Panic detected! Confidence: ${(data.confidence * 100).toFixed(1)}%`
      );
    } else if (data.type === "wakeword") {
      addAlert("wakeword", "Wakeword detected!");
    }
  }, []);

  const addAlert = useCallback((type, message) => {
    const newAlert = { type, message, timestamp: Date.now() };
    setAlerts((prev) => {
      // Keep only the most recent 5 alerts.
      const newAlerts = [...prev, newAlert].slice(-5);
      return newAlerts;
    });
  }, []);

  // Auto-dismiss alerts after 5 seconds
  useEffect(() => {
    if (alerts.length === 0) return;
    const timer = setTimeout(() => {
      setAlerts((prev) => prev.slice(1));
    }, 5000);
    return () => clearTimeout(timer);
  }, [alerts]);

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Box sx={{ p: 3, height: "100vh" }}>
        <Grid container spacing={3}>
          {/* Left Panel */}
          <Grid item xs={12} md={8}>
            <Paper sx={{ p: 2, height: "80vh" }}>
              <Stack spacing={2} height="100%">
                <SystemStatusIndicator
                  status={systemStatus}
                  connection={connectionStatus}
                />
                <CanvasVisualizer ref={canvasRef} />
                <MonitoringControls
                  isMonitoring={isMonitoring}
                  onToggle={() => setIsMonitoring((prev) => !prev)}
                />
              </Stack>
            </Paper>
          </Grid>
          {/* Right Panel */}
          <Grid item xs={12} md={4}>
            <Paper sx={{ p: 2, height: "80vh", overflow: "auto" }}>
              <Typography variant="h6" gutterBottom>
                Recent Alerts
              </Typography>
              <AlertHistory alerts={alerts} />
            </Paper>
          </Grid>
        </Grid>
        <AlertNotifications alert={alerts[alerts.length - 1]} />
      </Box>
    </ThemeProvider>
  );
}

// Sub-components

const SystemStatusIndicator = ({ status, connection }) => (
  <Card>
    <CardContent>
      <Typography variant="h6" gutterBottom>
        System Status
      </Typography>
      <Stack spacing={1}>
        <StatusItem
          label="Connection"
          status={connection === "connected" ? "active" : "inactive"}
        />
        <StatusItem
          label="Wakeword Model"
          status={status.wakewordModel ? "active" : "inactive"}
        />
        <StatusItem
          label="Panic Detection Model"
          status={status.panicModel ? "active" : "inactive"}
        />
        <StatusItem
          label="Audio Input"
          status={status.audioInput ? "active" : "inactive"}
        />
      </Stack>
    </CardContent>
  </Card>
);

const StatusItem = ({ label, status }) => (
  <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
    <Box
      sx={{
        width: 10,
        height: 10,
        borderRadius: "50%",
        bgcolor: status === "active" ? "success.main" : "error.main",
      }}
    />
    <Typography variant="body2">{label}</Typography>
  </Box>
);

const CanvasVisualizer = React.forwardRef((props, ref) => (
  <canvas
    ref={ref}
    style={{
      width: "100%",
      height: "200px",
      borderRadius: "8px",
      backgroundColor: theme.palette.background.default,
    }}
  />
));

const MonitoringControls = ({ isMonitoring, onToggle }) => (
  <Box sx={{ display: "flex", justifyContent: "center", gap: 2 }}>
    <Button
      variant="contained"
      color={isMonitoring ? "secondary" : "primary"}
      startIcon={isMonitoring ? <MicOff /> : <Mic />}
      onClick={onToggle}
      size="large"
    >
      {isMonitoring ? "Stop Monitoring" : "Start 24/7 Monitoring"}
    </Button>
    <IconButton color="inherit">
      <Settings />
    </IconButton>
  </Box>
);

const AlertHistory = ({ alerts }) => (
  <Stack spacing={1}>
    {alerts.map((alert, index) => (
      <Alert
        key={index}
        severity={
          alert.type === "error"
            ? "error"
            : alert.type === "panic"
            ? "warning"
            : "info"
        }
        iconMapping={{
          warning: <Warning fontSize="inherit" />,
          info: <NotificationsActive fontSize="inherit" />,
        }}
        sx={{ mb: 1 }}
      >
        <Typography variant="body2">
          {new Date(alert.timestamp).toLocaleTimeString()}: {alert.message}
        </Typography>
      </Alert>
    ))}
  </Stack>
);

const AlertNotifications = ({ alert }) => (
  <Snackbar
    open={Boolean(alert)}
    anchorOrigin={{ vertical: "bottom", horizontal: "right" }}
  >
    {alert && (
      <Alert
        severity={
          alert.type === "error"
            ? "error"
            : alert.type === "panic"
            ? "warning"
            : "info"
        }
        elevation={6}
        variant="filled"
      >
        {alert.message}
      </Alert>
    )}
  </Snackbar>
);

export default App;
