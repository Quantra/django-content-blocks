// Set the status in the status bar for a few seconds and set the status in the loader

const statusEle = document.getElementById("statusMessage");
const defaultMessage = statusEle.innerHTML;
const statusLoaderEle = document.getElementById("statusMessageLoader");
const statusDisplayTime = 5500;
let statusTimeout;

function fadeSwap(ele, text) {
  ele.animate([{ opacity: 1 }, { opacity: 0 }], {
    duration: 300,
  }).onfinish = function () {
    ele.innerHTML = text;
    ele.animate([{ opacity: 0 }, { opacity: 1 }], {
      duration: 300,
    });
  };
}
function showStatus(message) {
  // Show the given status message
  window.clearTimeout(statusTimeout);

  fadeSwap(statusLoaderEle, message);
  fadeSwap(statusEle, message);

  statusTimeout = window.setTimeout(function () {
    fadeSwap(statusEle, defaultMessage);
  }, statusDisplayTime);
}
