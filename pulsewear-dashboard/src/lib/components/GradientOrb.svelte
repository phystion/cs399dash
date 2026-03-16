<script lang="ts">
  // no props
</script>

<div class="orb-container" aria-hidden="true">
  <div class="orb orb-1"></div>
  <div class="orb orb-2"></div>
  <div class="orb orb-3"></div>
</div>

<style>
  .orb-container {
    position: fixed;
    inset: 0;
    pointer-events: none;
    z-index: 0;
    overflow: hidden;
  }
  .orb {
    position: absolute;
    border-radius: 50%;
    filter: blur(80px);
    opacity: 0.35;
  }
  .orb-1 {
    width: 600px; height: 600px;
    background: radial-gradient(circle, #38BDF8, #6366F1);
    top: -150px; left: -150px;
    animation: float-orb-1 18s ease-in-out infinite;
  }
  .orb-2 {
    width: 500px; height: 500px;
    background: radial-gradient(circle, #6366F1, #BAE6FD);
    bottom: -100px; right: -100px;
    animation: float-orb-2 22s ease-in-out infinite;
  }
  .orb-3 {
    width: 400px; height: 400px;
    background: radial-gradient(circle, #BAE6FD, #38BDF8);
    top: 40%; left: 50%;
    transform: translate(-50%, -50%);
    animation: float-orb-3 26s ease-in-out infinite;
  }
  @keyframes float-orb-1 {
    0%, 100% { transform: translate(0, 0) scale(1); }
    33%       { transform: translate(60px, -40px) scale(1.08); }
    66%       { transform: translate(-30px, 50px) scale(0.94); }
  }
  @keyframes float-orb-2 {
    0%, 100% { transform: translate(0, 0) scale(1); }
    33%       { transform: translate(-70px, 30px) scale(1.05); }
    66%       { transform: translate(40px, -60px) scale(0.96); }
  }
  @keyframes float-orb-3 {
    0%, 100% { transform: translate(-50%, -50%) scale(1); }
    33%       { transform: translate(calc(-50% + 50px), calc(-50% + 60px)) scale(0.92); }
    66%       { transform: translate(calc(-50% - 60px), calc(-50% - 20px)) scale(1.06); }
  }
</style>
