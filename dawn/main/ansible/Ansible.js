import { ipcMain } from 'electron';
import ProtoBuf from 'protobufjs';
import RendererBridge from '../RendererBridge';
import dgram from 'dgram';
import _ from 'lodash';
import { clearConsole, updateConsole } from '../../renderer/actions/ConsoleActions';
import {
    ansibleConnect,
    ansibleDisconnect,
    updateStatus,
} from '../../renderer/actions/InfoActions';
import { updatePeripheral } from '../../renderer/actions/PeripheralActions';

const runtimeIP = 'localhost';  // '192.168.128.22';
const clientPort = 1236; // send port
const serverPort = 1235; // receive port
const tcpPort = 1237;
const client = dgram.createSocket('udp4'); // sender
const server = dgram.createSocket('udp4'); // receiver

const protoFolder = '../ansible-protos'; // Location of protobuf definitions.
const dawnBuilder = ProtoBuf.loadProtoFile(`${protoFolder}/ansible.proto`);
const DawnData = dawnBuilder.build('DawnData');
const StudentCodeStatus = DawnData.StudentCodeStatus;

const runtimeBuilder = ProtoBuf.loadProtoFile(`${protoFolder}/runtime.proto`);
const RuntimeData = runtimeBuilder.build('RuntimeData');
const TCPData = runtimeBuilder.build('TCPData');

const net = require('net');
net.createServer((socket) => {
  console.log('TCP Connection Up');
  socket.on('data', (data) => {
    const console = TCPData.decode(data);
    RendererBridge.reduxDispatch(clearConsole());
    RendererBridge.reduxDispatch(updateConsole(console));
  });

  // Remove the client from the list when it leaves
  socket.on('end', () => {
    console.log('TCP Connection Ended');
  });
}).listen(tcpPort);


/**
 * Serialize the data using protocol buffers.
 */
function buildProto(data) {
  const status = data.studentCodeStatus ?
    StudentCodeStatus.TELEOP : StudentCodeStatus.IDLE;
  const gamepads = _.map(_.toArray(data.gamepads), (gamepad) => {
    const axes = _.toArray(gamepad.axes);
    const buttons = _.map(_.toArray(gamepad.buttons), Boolean);
    const GamepadMsg = new DawnData.Gamepad({
      index: gamepad.index,
      axes,
      buttons,
    });
    return GamepadMsg;
  });
  const message = new DawnData({
    student_code_status: status,
    gamepads,
  });
  return message;
}

/**
 * Receives data from the renderer process and sends that data
 * (serialized by protobufs) to the robot Runtime
 */
ipcMain.on('stateUpdate', (event, data) => {
  const message = buildProto(data);
  const buffer = message.encode().toBuffer();
  // Send the buffer over UDP to the robot.
  client.send(buffer, clientPort, runtimeIP, (err) => {
    if (err) {
      console.error('UDP socket error on send:', err);
    }
  });
});

/**
 * Handler to receive messages from the robot Runtime
 */
server.on('message', (msg) => {
  RendererBridge.reduxDispatch(ansibleConnect());
  RendererBridge.reduxDispatch(updateStatus());
  try {
    const data = RuntimeData.decode(msg);
    // console.log(`Dawn received: ${JSON.stringify(data)}\n`);
    for (const sensor of data.sensor_data) {
      RendererBridge.reduxDispatch(updatePeripheral(sensor));
    }
  } catch (e) {
    console.log(`Error decoding: ${e}`);
  }
});

server.on('error', (err) => {
  console.log(`Server error:\n${err.stack}`);
  server.close();
});

server.on('close', () => {
  RendererBridge.reduxDispatch(ansibleDisconnect());
  console.log('Server Closed');
});

server.bind(serverPort);
