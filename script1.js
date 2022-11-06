let svg = document.getElementById("bgart");

function drawCircles() {
  for (i = 0; i < 5; i++) {
    circle = document.createElementNS("http://www.w3.org/2000/svg", "circle");
    circle.setAttribute("r", Math.floor(Math.random() * 900) + 30);
    circle.setAttribute("cx", Math.floor(Math.random() * 900));
    circle.setAttribute("cy", Math.floor(Math.random() * 900));
    circle.setAttribute("stroke-width", Math.floor(Math.random() * 400 + 15));

    function getRandomLength() {
      return Math.floor(Math.random() * 500 + 100);
    }
    function getRandomGap() {
      return Math.floor(Math.random() * 500 + 900);
    }
    circle.setAttribute(
      "stroke-dasharray",
      `${getRandomLength()} ${getRandomGap()}`
    );

    svg.appendChild(circle);
  }
}

function removeAll() {
  while (svg.firstChild) {
    svg.removeChild(svg.lastChild);
  }
}

svg.addEventListener("click", function () {
  removeAll();
  drawCircles();
});

drawCircles();