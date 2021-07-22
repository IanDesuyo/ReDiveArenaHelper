import React, { useState } from "react";
import { makeStyles } from "@material-ui/core/styles";
import CssBaseline from "@material-ui/core/CssBaseline";
import Container from "@material-ui/core/Container";
import Typography from "@material-ui/core/Typography";
import Sidebar from "./components/Sidebar";
import WindowSelecter from "./components/WindowSelecter";
import GameView from "./components/GameView";

const useStyles = makeStyles(theme => ({
  container: {
    marginTop: theme.spacing(4),
  },
  root: {
    display: "flex",
  },
}));

function App() {
  const classes = useStyles();
  const [isRunning, setRunning] = useState({ status: 0, window: null, autoTeam: false });

  function handleSidebarClick(event) {
    console.log("sidebar clicked", event);
    if (event === "status" && isRunning.status === 1) {
      setRunning(prev => ({ ...prev, status: 0, window: null }));
    } else if (event === "autoTeam") {
      setRunning(prev => ({ ...prev, autoTeam: !prev.autoTeam }));
    }
  }
  async function setWindow(target_window) {
    const resp = await window.eel.set_window(target_window.hwnd)();
    if (!resp.error) {
      setRunning(prev => ({ ...prev, status: 1, window: target_window }));
    } else {
      console.log("set window error", resp.message);
      setRunning(prev => ({ ...prev, status: 0, window: null, error: resp.message }));
    }
  }
  function onError(error) {
    if (error === "window unsupport") {
      setRunning(prev => ({ ...prev, status: 2, error: error }));
    }
  }

  return window.eel ? (
    <div className={classes.root}>
      <CssBaseline />
      <Sidebar onClick={handleSidebarClick} isRunning={isRunning} />
      <Container className={classes.container}>
        {isRunning.status === 1 ? (
          <GameView isRunning={isRunning} onError={onError} />
        ) : (
          <WindowSelecter setWindow={setWindow} />
        )}
      </Container>
    </div>
  ) : (
    <Typography>
      無法與EEL連線...
      <br />
      {JSON.stringify(window.eel)}
    </Typography>
  );
}

export default App;
