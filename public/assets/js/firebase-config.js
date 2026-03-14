// Firebase Configuration (Compat version for script tags)
const firebaseConfig = {
    apiKey: "AIzaSyCP-VFbYpf66AXtMtVKQcjYCxAzsWxBp3w",
    authDomain: "osool-6ff25.firebaseapp.com",
    projectId: "osool-6ff25",
    storageBucket: "osool-6ff25.firebasestorage.app",
    messagingSenderId: "995130987286",
    appId: "1:995130987286:web:6d81177c3f6b8488d3f637",
    measurementId: "G-K3EET77W04"
};

// Initialize Firebase
if (typeof firebase !== 'undefined') {
    firebase.initializeApp(firebaseConfig);
    window.db = firebase.firestore();
    console.log("🔥 Firebase initialized successfully");
} else {
    console.error("❌ Firebase SDK not found!");
}
