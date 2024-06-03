<script>
import { useMqttStore } from "@/stores/mqtt.js";

export default {
  name: "DashboardCanvasView",
  props: {
    changesLocked: { required: false, type: Boolean, default: false },
  },
  data() {
    return {
      FPS: 24, // Animation Frames per second
      speed: 0.03, // Arrowhead speed
      arrowLength: 25,
      arrowWidth: 13,

      mqttStore: useMqttStore(),
      images: {
        evu: new Image(),
        pv: new Image(),
        house: new Image(),
        battery: new Image(),
        charge: new Image()
      },
    };
  },
  computed: {
    gridPower() {
      return parseFloat(this.mqttStore.getGridPower.replace('W', '').replace(',', ''));
    },
    pvPower() {
      return parseFloat(this.mqttStore.getPvPower.replace('W', '').replace(',', ''));
    },
    homePower() {
      return parseFloat(this.mqttStore.getHomePower.replace('W', '').replace(',', ''));
    },
    batteryPower() {
      return parseFloat(this.mqttStore.getBatteryPower.replace('W', '').replace(',', ''));
    },
    chargePoint1Power() {
      return parseFloat(this.mqttStore.getChargePointPower(2).replace('W', '').replace(',', ''));
    },
    chargePoint2Power() {
      return parseFloat(this.mqttStore.getChargePointPower(3).replace('W', '').replace(',', ''));
    }
  },
  methods: {
    drawDiagram() {
      const canvas = this.$refs.canvas;
      if (!canvas) return;
      const ctx = canvas.getContext('2d');
      ctx.clearRect(0, 0, canvas.width, canvas.height);

      // Draw components
      this.drawComponent(ctx, 150, 50, 'EVU', this.gridPower);
      this.drawComponent(ctx, 450, 50, 'PV', this.pvPower);
      this.drawComponent(ctx, 150, 215, 'Haus', this.homePower);
      this.drawComponent(ctx, 450, 215, 'Speicher', this.batteryPower);
      this.drawComponent(ctx, 150, 350, 'Ladepunkt-1', this.chargePoint1Power);
      this.drawComponent(ctx, 450, 350, 'Ladepunkt-2', this.chargePoint2Power);
      // Draw static white line connections
      // EVU & PV
      this.drawStaticLines(ctx, 150, 125, 300, 125);
      this.drawStaticLines(ctx, 150, 85, 150, 125);
      this.drawStaticLines(ctx, 300, 125, 450, 125);
      this.drawStaticLines(ctx, 450, 85, 450, 125);
      // joining line to house & battery
      this.drawStaticLines(ctx, 300, 125, 300, 215);
      // House & Battery
      this.drawStaticLines(ctx, 300, 215, 415, 215);
      this.drawStaticLines(ctx, 185, 215, 300, 215);
      // joining line to charge points
      this.drawStaticLines(ctx, 300, 215, 300, 350);
      // Chargers
      this.drawStaticLines(ctx, 185, 350, 300, 350);
      this.drawStaticLines(ctx, 300, 350, 415, 350);
    },
    drawComponent(ctx, x, y, label, power) {
      // Draw cirles
      ctx.fillStyle = '#222';
      ctx.beginPath();
      ctx.arc(x, y, 35, 0, Math.PI * 2, true);
      ctx.fill();
      ctx.strokeStyle = 'white';
      ctx.lineWidth = 2;
      ctx.stroke();
      //Draw svg images
      let img;
      let scaleFactor;
      switch (label) {
        case 'EVU':
          img = this.images.evu;
          scaleFactor = 0.14;
          break;
        case 'PV':
          img = this.images.pv;
          scaleFactor = 0.1;
          break;
        case 'Haus':
          img = this.images.house;
          scaleFactor = 0.09;
          break;
        case 'Speicher':
          img = this.images.battery;
          scaleFactor = 0.09;
          break;
        case 'Ladepunkt-1':
        case 'Ladepunkt-2':
          img = this.images.charge;
          scaleFactor = 0.07;
          break;
      }

      if (img) {
        const baseSize = Math.min(ctx.canvas.width, ctx.canvas.height); // Determine aspect ratio of the canvas.
        const imgWidth = scaleFactor * baseSize;  // scale img
        const imgHeight = scaleFactor * baseSize; //scale img
        ctx.drawImage(img, x - imgWidth / 2, y - imgHeight / 2, imgWidth, imgHeight); //place img at component center
      }
      //Draw label text left side
      if (x < 200) {
        ctx.textAlign = 'right';
        ctx.fillStyle = 'white';
        ctx.fillText(label, x - 50, y - 10);
        ctx.fillStyle = '#c9a68f';
        ctx.fillText(`${power} W`, x - 50, y + 10);
        //Draw label text right side  
      } else {
        ctx.textAlign = 'left';
        ctx.font = '15px Arial';
        ctx.fillStyle = 'white';
        ctx.fillText(label, x + 50, y - 10);
        ctx.fillStyle = '#c9a68f';
        ctx.fillText(`${power} W`, x + 50, y + 10);
      }
    },
    drawStaticLines(ctx, x1, y1, x2, y2) {
      ctx.strokeStyle = 'white';
      ctx.lineWidth = 3;
      ctx.beginPath();
      ctx.moveTo(x1, y1);
      ctx.lineTo(x2, y2);
      ctx.stroke();
    },
    animateArrows() {
      const canvas = this.$refs.canvas;
      if (!canvas) return;
      const ctx = canvas.getContext('2d');

      const drawLine = (x1, y1, x2, y2) => {
        ctx.strokeStyle = 'green';
        ctx.lineWidth = 2.5;
        ctx.beginPath();
        ctx.moveTo(x1, y1);
        ctx.lineTo(x2, y2);
        ctx.stroke();
      };

      const drawArrowhead = (x, y, angle) => {
        ctx.save();
        ctx.translate(x, y);
        ctx.rotate(angle);

        ctx.beginPath();
        ctx.moveTo(0, 0);
        ctx.lineTo(-this.arrowLength, this.arrowWidth / 2);
        ctx.lineTo(-this.arrowLength, -this.arrowWidth / 2);
        ctx.closePath();

        ctx.restore();
        ctx.fillStyle = 'green';
        ctx.fill();
      };

      const animateLine = (x1, y1, x2, y2, t) => {
        const totalLength = Math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2);
        const maxProgress = totalLength / (totalLength + this.arrowLength); // Calculate the maximum progress to stop the tip at the end
        let progress = (t * totalLength) / totalLength;
        if (progress > maxProgress) {
          progress = 0; // Reset progress if it exceeds maxProgress
        }
        let angle = Math.atan2(y2 - y1, x2 - x1);
        // Adjust position to move arrowhead forward along the line
        let x = x1 + progress * (x2 - x1) + Math.cos(angle) * this.arrowLength;
        let y = y1 + progress * (y2 - y1) + Math.sin(angle) * this.arrowLength;
        drawLine(x1, y1, x2, y2);
        drawArrowhead(x, y, angle);
        return t + this.speed;
      };
      // Set the desired Frames per second for the amnimation
      const interval = 1000 / this.FPS; // Interval in milliseconds
      let lastTime = (new Date()).getTime();
      let t1 = 0, t2 = 0, t3 = 0, t4 = 0, t5 = 0, t6 = 0, t7 = 0, t8 = 0, t9 = 0, t10 = 0, t11 = 0, t12 = 0, t13 = 0;
      // Call the animateLine function based on energy flows
      const animate = () => {
        const currentTime = (new Date()).getTime();
        const deltaTime = currentTime - lastTime;
        //FPS refresh time reached
        if (deltaTime > interval) {
          lastTime = currentTime - (deltaTime % interval);
          ctx.clearRect(0, 0, canvas.width, canvas.height);
          this.drawDiagram();

          if (this.chargePoint1Power > 0) {
            t1 = animateLine(300, 350, 185, 350, t1);
            if (t1 > 1) t1 = 0;
            t4 = animateLine(300, 215, 300, 350, t4);
            if (t4 > 1) t4 = 0;
          }

          if (this.chargePoint2Power > 0) {
            t2 = animateLine(300, 350, 415, 350, t2);
            if (t2 > 1) t2 = 0;
            t9 = animateLine(300, 215, 300, 350, t9);
            if (t9 > 1) t9 = 0;
          }

          if (this.homePower > 0) {
            t3 = animateLine(300, 215, 185, 215, t3);
            if (t3 > 1) t3 = 0;
          }

          if (this.homePower > 0 || this.chargePoint1Power > 0 || this.bhargePoint2Power > 0) {
            t8 = animateLine(300, 125, 300, 215, t8);
            if (t8 > 1) t8 = 0;
          }

          if (this.batteryPower > 0) {
            t5 = animateLine(300, 215, 415, 215, t5);
            if (t5 > 1) t5 = 0;
          }

          if (this.batteryPower < 0) {
            t5 = animateLine(415, 215, 300, 215, t5);
            if (t5 > 1) t5 = 0;
          }

          if (this.pvPower > 30) {
            t6 = animateLine(450, 125, 300, 125, t6);
            if (t6 > 1) t6 = 0;
            t7 = animateLine(450, 85, 450, 125, t7);
            if (t7 > 1) t7 = 0;
          }

          if (this.gridPower > 0) {
            t10 = animateLine(150, 125, 300, 125, t10);
            if (t10 > 1) t10 = 0;
            t11 = animateLine(150, 85, 150, 125, t11);
            if (t11 > 1) t11 = 0;
          }

          if (this.gridPower < 0) {
            t12 = animateLine(300, 125, 145, 125, t12);
            if (t12 > 1) t12 = 0;
            t13 = animateLine(145, 125, 145, 85, t13);
            if (t13 > 1) t13 = 0;
          }
        }
        requestAnimationFrame(animate);
      };
      animate();
    },
  },
  mounted() {
    this.images.evu.src = './icons/owbEVU.svg';
    this.images.pv.src = './icons/owbPV.svg';
    this.images.house.src = './icons/owbHouse.svg';
    this.images.battery.src = './icons/owbBattery.svg';
    this.images.charge.src = './icons/owbCharge.svg';
    this.images.charge.onload = () => {
      this.drawDiagram();
      this.animateArrows();
    };
  },
  beforeDestroy() {
    // Clear animation frames on component destroy
    if (this.animationFrameId) {
      cancelAnimationFrame(this.animationFrameId);
      this.animationFrameId = null;
    }
    // Nullify the canvas reference to prevent accessing it after destruction
    if (this.$refs.canvas) {
      this.$refs.canvas = null;
    }
  }
}
</script>

<template>
  <div class="canvas-container">
    <canvas ref="canvas" width="600px" height="400"></canvas>
  </div>
</template>

<style scoped>
.canvas-container {
  position: relative;
  width: 100%;
  margin-top: 0.5rem;
  padding-bottom: 66.67%;
  /* Aspect ratio 3:2 (height / width * 100) */
  background-color: #46444c;
  border-radius: 5px;
}

canvas {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  display: block;
}

@media only screen and (max-width: 800px) {
  .canvas-container {
    padding-bottom: 66.67%;
    /* Maintain aspect ratio */
  }
}
</style>