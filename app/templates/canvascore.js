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

const goat_imgs = [
  {% for g_img in goat_imgs %}
  '{{ g_img | e }}',
  {% endfor %}
];
const goatLocations = [];
sendQuery(
  `{userByName(name: "{{ username }}") {
      id,
      goats {
        edges {
          node {
            id
            originalOwner {
              id
              goatvatar
            }
          }
        }
      }
    }
  }`
).then((json) => {
  json.data.userByName.goats.edges.forEach(({node}) => {
    drawGoatAtRandomPoint(node.originalOwner.goatvatar, node.id);
  });
})
.catch((json) => {
  console.error(json);
});

function drawGoatAtRandomPoint(gType, id) {
  const margin = 50;
  const flip = Math.random() > 0.5;
  const rX = margin + Math.random() * (width - margin*2);
  const rY = margin + Math.random() * (height - margin*2);
  const img = new Image();
  img.onload = function() {
    if (flip) {
      drawFlipped(img, rX, rY);
    } else {
      ctx.drawImage(img, rX, rY);
    }
    goatLocations.push([rX + img.width/2, rY + img.height/2, id]);
  }
  img.src = `data:image/png;base64,${goat_imgs[gType-1]}`;
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
    console.error('didClick() is unimplemented');
  }
});