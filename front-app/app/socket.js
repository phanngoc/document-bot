import { io } from 'socket.io-client';

const socket = io('http://localhost:5002');  // Adjust the server URL if necessary

socket.on('connect', () => {
  console.log('Connected to the server');
});

socket.on('disconnect', () => {
  console.log('Disconnected from the server');
});

export default socket;
