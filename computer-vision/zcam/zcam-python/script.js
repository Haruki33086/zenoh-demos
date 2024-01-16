// 初期化
let restApiBase = 'http://13.208.62.139:8000/';
let subScope = 'simu';
const TOPIC_LOGS = "/rt/rosout";
const TOPIC_DRIVE = "/rt/turtle1/cmd_vel";
const Http = new XMLHttpRequest(); // HTTP client

// ボタン押下で実行されるアクションと、そのアクションを繰り返すためのタイマーIDを保持する変数
let repeatActionTimer = null;

// ボタン押下イベントのハンドラー
const buttonDownActions = {
    'move-forward': () => startRepeatingAction(() => pubTwist(1.0, 0.0)),
    'move-left': () => startRepeatingAction(() => pubTwist(0.0, 1.0)),
    'move-stop': () => startRepeatingAction(() => pubTwist(0.0, 0.0)),
    'move-right': () => startRepeatingAction(() => pubTwist(0.0, -1.0)),
    'move-backward': () => startRepeatingAction(() => pubTwist(-1.0, 0.0))
};

// ボタン押下時に連続してアクションを実行する関数
function startRepeatingAction(action) {
    stopRepeatingAction(); // 既存のアクションを停止
    action();
    repeatActionTimer = setInterval(action, 100); // 100ミリ秒ごとにアクションを繰り返す
}

// ボタン離上時に連続アクションを停止する関数
function stopRepeatingAction() {
    if (repeatActionTimer !== null) {
        clearInterval(repeatActionTimer);
        repeatActionTimer = null;
    }
}

// ボタン離上イベントのハンドラー
const buttonUpAction = () => {
    stopRepeatingAction();
    pubTwist(0.0, 0.0); // 停止コマンドを送信
};

Object.keys(buttonDownActions).forEach(id => {
    const button = document.getElementById(id);
    button.addEventListener('mousedown', buttonDownActions[id]);
    button.addEventListener('mouseup', buttonUpAction);
    button.addEventListener('mouseleave', buttonUpAction); // ボタンからマウスが離れた場合も考慮
});

// 折りたたみセクションの表示切替機能
function toggleSection(sectionId) {
    var section = document.getElementById(sectionId);
    section.style.display = section.style.display === 'block' ? 'none' : 'block';
}

// Twistメッセージの発行
function pubTwist(linear, angular) {
    // スケール値の取得
    var linear_scale = document.getElementById("linear-scale").value;
    var angular_scale = document.getElementById("angular-scale").value;

    // Twistメッセージの作成
    var twist = new Twist(new Vector3(linear * linear_scale, 0.0, 0.0), new Vector3(0.0, 0.0, angular * angular_scale));
    var writer = new jscdr.CDRWriter();
    twist.encode(writer);

    // REST APIを介してcmd_velトピックに発行
    var key_expr = subScope + TOPIC_DRIVE;
    Http.open('PUT', restApiBase + key_expr, true);
    Http.setRequestHeader('Content-Type', 'application/octet-stream');
    Http.send(writer.buf.buffer);
}

// スライダーの値表示を更新するイベントリスナー
const sliderActions = {
    'linear-scale': (e) => updateValueDisplay('linear-value', e.target.value),
    'angular-scale': (e) => updateValueDisplay('angular-value', e.target.value),
    'rest-api-url-value': (e) => { restApiBase = e.target.value; setCameraImage(); },
    'sub-scope-value': (e) => { subScope = e.target.value; setCameraImage(); }
};

Object.keys(sliderActions).forEach(id => {
    document.getElementById(id).addEventListener('input', sliderActions[id]);
});

// スライダーの値表示を更新
function updateValueDisplay(elementId, value) {
    document.getElementById(elementId).textContent = value;
}

document.addEventListener("DOMContentLoaded", function() {
    setCameraImage();
});

// カメラ画像の設定
function setCameraImage() {
    let cameraImgElem = document.getElementById("camera-img");
    let realsenseImgElem = document.getElementById("realsense-img");
    if (cameraImgElem) {
        let imgURL = restApiBase.replace(":8000", ":8080") + subScope + "/camera?_method=SUB";
        cameraImgElem.src = imgURL;
    }
    if (realsenseImgElem) {
        let imgURL = restApiBase.replace(":8000", ":8080") + subScope + '1' + "/camera?_method=SUB";
        realsenseImgElem.src = imgURL;
    }
}

// キーボードイベントの処理
document.onkeydown = (e) => {
    switch(e.key) {
        case 'ArrowUp': pubTwist(1.0, 0.0); break;
        case 'ArrowDown': pubTwist(-1.0, 0.0); break;
        case 'ArrowLeft': pubTwist(0.0, 1.0); break;
        case 'ArrowRight': pubTwist(0.0, -1.0); break;
        case ' ': pubTwist(0.0, 0.0); break;
    }
};

document.onkeyup = (e) => {
    if (['ArrowLeft', 'ArrowUp', 'ArrowRight', 'ArrowDown'].includes(e.key)) {
        pubTwist(0.0, 0.0);
    }
};

// ROS2ログの購読
if (typeof (EventSource) !== "undefined") {
    var key_expr = subScope + TOPIC_LOGS;
    ros2_logs_source = new EventSource(restApiBase + key_expr);
    ros2_logs_source.addEventListener("PUT", e => {
        let sample = JSON.parse(e.data);
        let reader = new jscdr.CDRReader(dcodeIO.ByteBuffer.fromBase64(sample.value));
        let log = Log.decode(reader);
        let elem = document.getElementById("log-messages");
        elem.innerHTML += `ROS2: [${log.time.sec}.${log.time.nsec}] [${log.name}]: ${log.msg}<br>`;
        elem.scrollTop = elem.scrollHeight;
    });
} else {
    document.getElementById("logs-messages").innerHTML = "お使いのブラウザはサーバー送信イベントをサポートしていません...";
}

/////////////////////////////////////////////////////////////
// ROS2 Types declaration with CDR encode/decode functions //
/////////////////////////////////////////////////////////////

// ROS2 Time type
class Time {
    constructor(sec, nsec) {
        this.sec = sec;
        this.nsec = nsec;
    }

    static decode(cdrReader) {
        let sec = cdrReader.readInt32();
        let nsec = cdrReader.readUint32();
        return new Time(sec, nsec);
    }
}

// ROS2 Log type (received in 'rosout' topic)
class Log {
    constructor(time, level, name, msg, file, fn, line) {
        this.time = time;
        this.level = level;
        this.name = name;
        this.msg = msg;
        this.file = file;
        this.fn = fn;
        this.line = line;
    }

    static decode(cdrReader) {
        let time = Time.decode(cdrReader);
        let level = cdrReader.readByte();
        let name = cdrReader.readString();
        let msg = cdrReader.readString();
        let file = cdrReader.readString();
        let fn = cdrReader.readString();
        let line = cdrReader.readUint32();
        return new Log(time, level, name, msg, file, fn, line);
    }
}

// ROS2 Vector3 type
class Vector3 {
    constructor(x, y, z) {
        this.x = x;
        this.y = y;
        this.z = z;
    }

    encode(cdrWriter) {
        cdrWriter.writeFloat64(this.x);
        cdrWriter.writeFloat64(this.y);
        cdrWriter.writeFloat64(this.z);
    }

    static decode(cdrReader) {
        let x = cdrReader.readFloat64();
        let y = cdrReader.readFloat64();
        let z = cdrReader.readFloat64();
        return new Vector3(x, y, z);
    }
}

// ROS2 Twist type (published in 'cmd_vel' topic)
class Twist {
    constructor(linear, angular) {
        this.linear = linear;
        this.angular = angular;
    }

    encode(cdrWriter) {
        this.linear.encode(cdrWriter);
        this.angular.encode(cdrWriter);
    }
}