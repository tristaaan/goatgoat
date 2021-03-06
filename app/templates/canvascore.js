function autoScale(el, ctx) {
  var devicePixelRatio = window.devicePixelRatio || 1
  var backingStore = ctx.backingStorePixelRatio ||
    ctx.webkitBackingStorePixelRatio ||
    ctx.mozBackingStorePixelRatio ||
    ctx.msBackingStorePixelRatio ||
    ctx.oBackingStorePixelRatio ||
    ctx.backingStorePixelRatio || 1;

  var ratio = (devicePixelRatio || 1) / backingStore;

  if (devicePixelRatio !== backingStore) {

    var oldWidth = el.width;
    var oldHeight = el.height;

    el.width = oldWidth * ratio;
    el.height = oldHeight * ratio;

    el.style.width = oldWidth + 'px';
    el.style.height = oldHeight + 'px';

    // now scale the context to counter
    // the fact that we've manually scaled
    // our canvas element
    ctx.scale(ratio, ratio);
  }
};

const canvas = document.getElementById('canvas');
const ctx = canvas.getContext('2d');
const width = 500;
const height = 500;

canvas.width = `${width}`;
canvas.height = `${height}`;
autoScale(canvas, ctx);

const goatImgStrs = [
  {% for g_img in goat_imgs %}
  '{{ g_img | e }}',
  {% endfor %}
];
const goatImgById = {};
let goatById = {};
let goatLocations = [];
sendQuery(
  `{userByName(name: "{{ username }}") {
      userId,
      goats {
        edges {
          node {
            goatId
            originalOwner {
              userId
              name
              goatvatar
            }
          }
        }
      }
    }
  }`
).then((json) => {
  json.data.userByName.goats.edges.forEach(({node}) => {
    drawGoatAtRandomPoint(node.originalOwner, node.goatId);
  });
})
.catch((json) => {
  console.error(json);
});

function drawGoatAtRandomPoint(origOwner, goatId) {
  const margin = 50;
  const flipped = Math.random() > 0.5;
  const rX = margin + Math.random() * (width - margin*2);
  const rY = margin + Math.random() * (height - margin*2);
  const imgId = origOwner.goatvatar-1;
  if (!goatImgById.hasOwnProperty(imgId)) {
    const img = new Image();
    img.onload = function() {
      drawGoatAtPoint(img, rX, rY, flipped);
      const center = [rX + img.width/2, rY + img.height/2, goatId];
      goatLocations.push(center);
      goatById[goatId] = {drawLoc: [rX, rY], center, origOwner, flipped};
      goatImgById[imgId] = img;
    }
    img.src = `data:image/png;base64,${goatImgStrs[imgId]}`;
  } else {
    const img = goatImgById[imgId];
    drawGoatAtPoint(img, rX, rY, flipped);
  }
}

function drawGoatAtPoint(img, x, y, flipped) {
  if (flipped) {
    drawFlipped(img, x, y);
  } else {
    ctx.drawImage(img, x, y);
  }
}

function selectGoat(x, y, color='green') {
  clear();
  ctx.fillStyle = color;
  ctx.beginPath();
  ctx.arc(x, y, 35, 0, 360);
  ctx.fill();
  redraw();
}

function removeGoatAndRedraw(goatIdToRemove) {
  delete goatById[goatIdToRemove];
  goatLocations = [];
  for (gid in goatById) {
    const center = goatById[gid];
    goatLocations.push(center);
  }
  clearAndRedraw();
}

function clearAndRedraw() {
  clear();
  redraw();
}

function clear() {
  ctx.clearRect(0, 0, width, height);
}

function redraw() {
  for (gid in goatById) {
    const {drawLoc, origOwner, flipped} = goatById[gid];
    const [x,y] = drawLoc;
    const imgId = origOwner.goatvatar-1;
    if (!goatImgById.hasOwnProperty(imgId)) {
      // not sure how this could run right now.
      const img = new Image();
      img.onload = function() {
        drawGoatAtPoint(img, x, y, flipped);
      }
      img.src = `data:image/png;base64,${goatImgStrs[imgId]}`;
    } else {
      drawGoatAtPoint(goatImgById[imgId], x, y, flipped);
    }
  }
}

function drawFlipped(img, x, y) {
  ctx.translate(x+img.width, y);
  ctx.scale(-1,1);
  ctx.drawImage(img,0,0);
  ctx.setTransform(1,0,0,1,0,0);
}

function distance(x1, y1, x2, y2) {
  const a = x1-x2;
  const b = y1-y2;
  return Math.sqrt((a * a) + (b * b));
}

function goatsNearClick(x,y) {
  const margin = 50;
  const ret = [];
  for ([gX, gY, id] of goatLocations) {
    if (distance(x, y, gX, gY) < margin) {
      ret.push(id);
    }
  }
  return ret;
}

canvas.addEventListener('click', (e) => {
  const x = e.pageX - canvas.offsetLeft;
  const y = e.pageY - canvas.offsetTop;
  try {
    didClick(x,y);
  } catch (e) {
    console.error(e);
  }
});