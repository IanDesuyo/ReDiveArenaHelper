import { useEffect, useState } from "react";
import Card from "@material-ui/core/Card";
import CardContent from "@material-ui/core/CardContent";
import Typography from "@material-ui/core/Typography";
import Divider from "@material-ui/core/Divider";
import List from "@material-ui/core/List";
import ListItem from "@material-ui/core/ListItem";

export default function WindowSelecter(props) {
  const { setWindow } = props;
  const [windows, setWindows] = useState([]);

  useEffect(() => {
    async function getWindows() {
      setWindows(await window.eel.get_windows()());
    }

    getWindows();
  }, []);
  return (
    <Card>
      <CardContent>
        <Typography variant="h5" gutterBottom>
          請選擇遊戲視窗
        </Typography>
        <Divider />
        <List>
          {windows.map((window, index) => (
            <ListItem
              button
              onClick={() => {
                setWindow(window);
              }}
              key={index}
            >
              <Typography>
                {window.hwnd} - {window.title}
              </Typography>
            </ListItem>
          ))}
        </List>
      </CardContent>
    </Card>
  );
}
