# chatgpt-slack-bot

Slack bot which interacts with ChatGPT.

# How to install

* Watch the following [Tech with Tim tutorials](https://youtu.be/KJ5bFv-IRFM), Part 1 to find out how to install python, the [NGROK proxy](https://ngrok.com/) and the Slack python modules. Watch [Part 2](https://youtu.be/6gHvqXrfjuo) and [Part 3](https://youtu.be/sEFx0b9y_Xo) for the Slack Bot Code.

* Install Flask and playwright. (playwright will ask you to "playwright install" once after actual install)

* Check out [Taranjeet Singh](https://github.com/taranjeet)'s [chatgpt-whatsapp-bot](https://github.com/taranjeet/chatgpt-whatsapp-bot) repo and [Daniel Gross](https://github.com/danielgross)'s [whatsapp-gpt](https://github.com/danielgross/whatsapp-gpt) repo for more info.

* Pay attention to [this code](https://stackoverflow.com/a/51027874/15223881), its very important due to Slacks 3 second limit on response time.

* Once everything is installed and configured, the order of initialization is:
    1. Start NGROK, then update your Slack app's Slack Endpoints on [api.slack.com]()
    1. run the bot.py file - I use [VS Code](https://code.visualstudio.com/) with the Python and Code Runner Extensions.
    3. Chat the bot in Slack. 