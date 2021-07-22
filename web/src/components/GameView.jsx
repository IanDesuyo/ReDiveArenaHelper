import { useEffect, useState } from "react";
import { makeStyles, withStyles } from "@material-ui/core/styles";
import Card from "@material-ui/core/Card";
import CardMedia from "@material-ui/core/CardMedia";
import Typography from "@material-ui/core/Typography";
import Grid from "@material-ui/core/Grid";
import CardContent from "@material-ui/core/CardContent";
import Button from "@material-ui/core/Button";
import Divider from "@material-ui/core/Divider";
import Backdrop from "@material-ui/core/Backdrop";
import CircularProgress from "@material-ui/core/CircularProgress";

const useStyles = makeStyles(theme => ({
  targetCard: {
    cursor: "pointer",
    position: "relative",
  },
}));

const LimitedBackdrop = withStyles({
  root: {
    position: "absolute",
    zIndex: 1,
  },
})(Backdrop);

export default function GameView(props) {
  const { isRunning, onError } = props;
  const classes = useStyles();
  const [data, setData] = useState({});
  const [ans, setAns] = useState({ 1: null, 2: null, 3: null });

  async function getGameView(detect = false) {
    let resp = await window.eel.get_game_view(detect)();
    if (!resp.error) {
      setData(prev => ({
        image: "data:image/jpeg;base64," + resp.image,
        targets: detect ? resp.targets : prev.targets,
      }));
    } else {
      onError("window unsupport");
      console.error(resp);
    }
  }

  async function getAttackTeam(index, def_units) {
    setAns(prev => ({ ...prev, [index]: "loading" }));
    let resp = await window.eel.get_attack_team(def_units)();
    if (!resp.error) {
      setAns(prev => ({ ...prev, [index]: resp }));
    } else {
      console.error(resp);
    }
  }

  async function doAttack(i) {
    let click = data.targets[i][0].click;
    let atk_units = isRunning.autoTeam ? ans[i].attack : null;
    let resp = await window.eel.do_attack(click, atk_units);
    if (!resp.error) {
      console.log("Good Luck");
    } else {
      console.error(resp);
    }
  }

  useEffect(() => {
    getGameView(true);
    const interval = setInterval(() => getGameView(), 3000);

    return () => {
      clearInterval(interval);
    };
  }, []);

  useEffect(() => {
    setAns({ 1: null, 2: null, 3: null });
  }, [data.targets]);

  return (
    <div>
      <Card>
        <CardMedia component="img" image={data.image} />
      </Card>
      <Typography variant="h5">敵方隊伍</Typography>
      <Button onClick={() => getGameView(true)}>更新</Button>
      <Grid container spacing={3}>
        {data.targets &&
          data.targets.map((target, i) => (
            <Grid item xs={4} key={i}>
              <Card
                className={classes.targetCard}
                onClick={() => {
                  ans[i] ? doAttack(i) : getAttackTeam(i, target);
                }}
              >
                <CardContent>
                  <Typography variant="body1" gutterBottom>
                    隊伍{i + 1}
                  </Typography>
                  <Divider />
                  <Grid container spacing={1}>
                    <Grid item xs={6}>
                      <Typography variant="body1" gutterBottom>
                        防禦隊伍
                      </Typography>
                      {target.map((unit, j) => (
                        <Typography key={j} variant="body1">
                          {unit.data.name_tw || unit.data.name_jp} ({unit.rarity}星)
                        </Typography>
                      ))}
                    </Grid>
                    <Grid item xs={6}>
                      {ans[i] && ans[i] !== "loading" ? (
                        <>
                          <Typography variant="body1" gutterBottom>
                            攻擊隊伍 ({ans[i].good}/{ans[i].bad})
                          </Typography>
                          {ans[i].attack.map((unit, j) => (
                            <Typography key={j} variant="body1">
                              {unit.data.name_tw || unit.data.name_jp}
                            </Typography>
                          ))}
                        </>
                      ) : (
                        <></>
                      )}
                    </Grid>
                  </Grid>
                  <LimitedBackdrop open={ans[i] === "loading"}>
                    <CircularProgress color="inherit" />
                  </LimitedBackdrop>
                </CardContent>
              </Card>
            </Grid>
          ))}
      </Grid>
    </div>
  );
}
