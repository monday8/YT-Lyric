from flask import Flask, request, jsonify
from flask_cors import CORS
import logging
import sys
from threading import Thread
from PyQt5.QtWidgets import QApplication
from AutoDlp import TrayApp
from globals import data_queue

app = Flask(__name__)
CORS(app)

@app.route('/video_content', methods=['POST'])
def update_video_content():
    data = request.json
    current_time = data['time']
    video_details = data['details']['videoId']
    
    # 將數據放入隊列
    data_queue.put((current_time, video_details))
    
    return jsonify({"status": "success"})

if __name__ == '__main__':
    def start_flask():
        # 設置Flask日誌級別為僅顯示錯誤
        log = logging.getLogger('werkzeug')
        log.setLevel(logging.ERROR)
        app.run(debug=False, use_reloader=False)
    
    # 啟動Flask服務器線程
    flask_thread = Thread(target=start_flask)
    flask_thread.start()

    app = QApplication(sys.argv)
    trayApp = TrayApp()
    trayApp.show()

    sys.exit(app.exec_())
