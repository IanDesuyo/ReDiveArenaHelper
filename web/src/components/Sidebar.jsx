import { makeStyles } from "@material-ui/core/styles";
import Drawer from "@material-ui/core/Drawer";
import Divider from "@material-ui/core/Divider";
import Typography from "@material-ui/core/Typography";
import List from "@material-ui/core/List";
import ListItem from "@material-ui/core/ListItem";
import ListItemText from "@material-ui/core/ListItemText";
import PopoverButton from "./PopoverButton";
import { version } from "../../package.json";

const useStyles = makeStyles(theme => ({
  running: {
    background: "#00C851",
    "&:hover": {
      background: "#007E33",
    },
  },
  stoped: {
    background: "#9ea7ad",
    "&:hover": {
      background: "#75818a",
    },
  },
  error: {
    background: "#ff4444",
    "&:hover": {
      background: "#CC0000",
    },
  },
  drawer: {
    width: 240,
    // flexShrink: 0,
  },
  drawerPaper: {
    width: 240,
  },
  popover: {
    pointerEvents: "none",
  },
  paper: {
    padding: theme.spacing(1),
  },
  version: {
    position: "fixed",
    width: 240,
    bottom: 0,
    paddingBottom: 10,
  },
}));

export default function Sidebar(props) {
  const { onClick, isRunning } = props;
  const classes = useStyles();

  return (
    <Drawer
      variant="persistent"
      anchor="left"
      open={true}
      className={classes.drawer}
      classes={{
        paper: classes.drawerPaper,
      }}
    >
      <ListItem button onClick={() => onClick("home")}>
        <Typography variant="h6" align="center">
          ReDive Arena Helper
        </Typography>
      </ListItem>
      <Divider />
      <List>
        <ListItem key="status">
          <PopoverButton
            buttonText={["未運行", "運行中", "錯誤"][isRunning.status]}
            buttonClassName={[classes.stoped, classes.running, classes.error][isRunning.status]}
            popoverText={
              [
                "請先選擇遊戲視窗",
                isRunning.window ? isRunning.window.title : null,
                isRunning.error,
              ][isRunning.status]
            }
            onClick={() => onClick("status")}
            fullWidth
          />
        </ListItem>
        <ListItem key="autoTeam">
          <PopoverButton
            buttonText="自動選隊"
            buttonClassName={isRunning.autoTeam ? classes.running : classes.stoped}
            popoverText={isRunning.autoTeam ? "自動選隊已開啟\n請小心翻車" : "請先詳閱公開說明書"}
            onClick={() => onClick("autoTeam")}
            fullWidth
          />
        </ListItem>
        <div className={classes.version}>
          <Divider />
          <ListItem button key="version" onClick={()=>window.open("https://github.com/IanDesuyo/ReDiveArenaHelper")}>
            <ListItemText>{`Version ${version}`}</ListItemText>
          </ListItem>
        </div>
      </List>
    </Drawer>
  );
}
