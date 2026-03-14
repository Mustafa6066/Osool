
import * as THREE from 'https://unpkg.com/three@0.160.0/build/three.module.js';

/* 
   ═══════════════════════════════════════════════════════════════════════════
   OSOOL HERO 3D SCENE
   Impl: Floating Glass Particles & Connecting Lines (Network Effect)
   ═══════════════════════════════════════════════════════════════════════════
*/

export function initHeroScene() {
    const container = document.getElementById('hero-canvas-container');
    if (!container) return;

    // SCENE SETUP
    const scene = new THREE.Scene();
    // Use clear background to blend with CSS gradient
    scene.background = null;

    // CAMERA
    const camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
    camera.position.z = 30;

    // RENDERER
    const renderer = new THREE.WebGLRenderer({ alpha: true, antialias: true });
    renderer.setSize(window.innerWidth, window.innerHeight);
    renderer.setPixelRatio(window.devicePixelRatio);
    container.appendChild(renderer.domElement);

    // PARTICLES (Properties represent "Nodes" in the network)
    const particleCount = 60;
    const geometry = new THREE.BufferGeometry();
    const positions = new Float32Array(particleCount * 3);
    const velocities = [];

    // Initialize positions
    for (let i = 0; i < particleCount * 3; i += 3) {
        positions[i] = (Math.random() - 0.5) * 50;     // x
        positions[i + 1] = (Math.random() - 0.5) * 50; // y
        positions[i + 2] = (Math.random() - 0.5) * 30; // z

        velocities.push({
            x: (Math.random() - 0.5) * 0.02,
            y: (Math.random() - 0.5) * 0.02,
            z: (Math.random() - 0.5) * 0.02
        });
    }

    geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));

    // MATERIAL (Gold/Luxurious points)
    const material = new THREE.PointsMaterial({
        color: 0xd4af37, // Luxury Gold
        size: 0.2,
        transparent: true,
        opacity: 0.8
    });

    const particles = new THREE.Points(geometry, material);
    scene.add(particles);

    // LINES (Connecting the nodes)
    const lineMaterial = new THREE.LineBasicMaterial({
        color: 0xd4af37,
        transparent: true,
        opacity: 0.15
    });

    // MOUSE INTERACTION
    let mouseX = 0;
    let mouseY = 0;
    let targetX = 0;
    let targetY = 0;

    const windowHalfX = window.innerWidth / 2;
    const windowHalfY = window.innerHeight / 2;

    document.addEventListener('mousemove', (event) => {
        mouseX = (event.clientX - windowHalfX) * 0.05;
        mouseY = (event.clientY - windowHalfY) * 0.05;
    });

    // RESIZE
    window.addEventListener('resize', () => {
        camera.aspect = window.innerWidth / window.innerHeight;
        camera.updateProjectionMatrix();
        renderer.setSize(window.innerWidth, window.innerHeight);
    });

    // ANIMATION LOOP
    function animate() {
        requestAnimationFrame(animate);

        targetX = mouseX * 0.001;
        targetY = mouseY * 0.001;

        // Gentle rotation based on mouse
        particles.rotation.y += 0.001 + (targetX - particles.rotation.y) * 0.05;
        particles.rotation.x += 0.001 + (targetY - particles.rotation.x) * 0.05;

        // Update particle positions
        const positions = particles.geometry.attributes.position.array;

        for (let i = 0; i < particleCount; i++) {
            const i3 = i * 3;

            positions[i3] += velocities[i].x;
            positions[i3 + 1] += velocities[i].y;
            positions[i3 + 2] += velocities[i].z;

            // Boundary check - bounce back
            if (positions[i3] > 25 || positions[i3] < -25) velocities[i].x *= -1;
            if (positions[i3 + 1] > 25 || positions[i3 + 1] < -25) velocities[i].y *= -1;
            if (positions[i3 + 2] > 15 || positions[i3 + 2] < -15) velocities[i].z *= -1;
        }

        particles.geometry.attributes.position.needsUpdate = true;

        renderer.render(scene, camera);
    }

    animate();
    console.log("✨ Three.js Hero Scene Initialized");
}
