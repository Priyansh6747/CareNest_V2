// Import the functions you need from the SDKs you need
import { initializeApp } from "firebase/app";
import { initializeAuth, getReactNativePersistence } from 'firebase/auth';
import ReactNativeAsyncStorage from '@react-native-async-storage/async-storage';
// TODO: Add SDKs for Firebase products that you want to use
// https://firebase.google.com/docs/web/setup#available-libraries

// Your web app's Firebase configuration
// For Firebase JS SDK v7.20.0 and later, measurementId is optional
const firebaseConfig = {
    apiKey: "AIzaSyA-xujIQWMOLZpHAxJzWe0HjLhGwjLbncQ",
    authDomain: "carenest-fcfff.firebaseapp.com",
    projectId: "carenest-fcfff",
    storageBucket: "carenest-fcfff.firebasestorage.app",
    messagingSenderId: "907038276342",
    appId: "1:907038276342:web:dde8a932afe88e1d408ad7",
    measurementId: "G-8F1T1Y22WW"
};

// Initialize Firebase
const app = initializeApp(firebaseConfig);
export const auth = initializeAuth(app, {
    persistence: getReactNativePersistence(ReactNativeAsyncStorage)
});