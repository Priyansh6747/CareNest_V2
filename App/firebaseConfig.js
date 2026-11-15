import { initializeApp, getApp, getApps } from "firebase/app";
import { getAuth, initializeAuth, getReactNativePersistence } from 'firebase/auth';
import ReactNativeAsyncStorage from '@react-native-async-storage/async-storage';

const firebaseConfig = {
    apiKey: "AIzaSyA-xujIQWMOLZpHAxJzWe0HjLhGwjLbncQ",
    authDomain: "carenest-fcfff.firebaseapp.com",
    projectId: "carenest-fcfff",
    storageBucket: "carenest-fcfff.firebasestorage.app",
    messagingSenderId: "907038276342",
    appId: "1:907038276342:web:dde8a932afe88e1d408ad7",
    measurementId: "G-8F1T1Y22WW"
};

export const app = getApps().length ? getApp() : initializeApp(firebaseConfig);

function createAuth() {
    try {
        return initializeAuth(app, {
            persistence: getReactNativePersistence(ReactNativeAsyncStorage),
        });
    } catch {
        return getAuth(app);
    }
}

export const auth = createAuth();
