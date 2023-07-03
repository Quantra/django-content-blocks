// todo test all this works

const popupEle = document.getElementById("popupBase");
const popupContentWrapperEle = document.getElementById("popupContentWrapper");
const popupContentEle = document.getElementById("popupContent");
const popupBtnClass = "popup-btn";
const popupConfirmBtnEle = document.getElementById("popupConfirmBtn");
let popupConfirmCallback;

popupEle.addEventListener("click", function (e) {
  // Fire the callback if the confirm button is clicked.
  if (e.target === popupConfirmBtnEle) {
    popupConfirmCallback();
  }

  // Close the callback on click away or if either button is clicked.
  if (!popupContentWrapperEle.contains(e.target) || e.target.classList.contains(popupBtnClass)) {
    hidePopup();
  }
});

function showPopup(popupContentID, confirmCallback, label) {
  // Set the callback for the confirm button
  popupConfirmCallback = confirmCallback;

  // Change the content of the popup
  let contentEle = document.getElementById(popupContentID);
  if (label !== undefined) {
    contentEle.getElementById("popupContentLabel").innerHTML = label + "?";
  }
  popupContentEle.innerHTML = contentEle.innerHTML;

  // Disable scrolling
  if (document.documentElement.scrollHeight > document.documentElement.clientHeight) {
    const scrollTop = document.documentElement.scrollTop;
    document.documentElement.classList.add("noscroll");
    document.documentElement.style.top = `${-scrollTop}px`;
  }

  // Show the popup
  popupEle.classList.remove("hidden");
}

function hidePopup() {
  // Enable scrolling
  let scrollTop = parseInt(document.documentElement.style.top.replace("px", ""));
  document.documentElement.classList.remove("noscroll");
  document.documentElement.scrollTop = -scrollTop;

  // Hide the popup
  popupEle.classList.add("hidden");
}

// todo delete below
// let $html, $body;
// let open_popups = { popups: [], callers: [] };
// let $popup_base;
//
// $(document).ready(function () {
//   $html = $("html");
//   $body = $("body");
//   $popup_base = $("#popup_base");
// });
//
// function showPopup(caller, kwargs) {
//   let default_kwargs = {
//     open_callback: undefined,
//     confirm_callback: undefined,
//     css_class: undefined,
//     content: undefined,
//   };
//   kwargs = $.extend({}, default_kwargs, kwargs);
//
//   if (open_popups.callers.includes(caller)) return false;
//
//   disableScroll();
//
//   let $popup = $popup_base.clone();
//   $popup.attr("id", "");
//   open_popups.popups.push($popup);
//   open_popups.callers.push(caller);
//
//   $popup
//     .on("click", function () {
//       hidePopup($popup);
//     })
//     .on("click", ".confirm", function () {
//       hidePopup($popup);
//       if (kwargs.confirm_callback) kwargs.confirm_callback($popup);
//     })
//     .on("click", ".close-popup", function () {
//       hidePopup($popup);
//     })
//     .on("click", ".popup-wrapper", function (e) {
//       e.stopPropagation();
//     });
//
//   if (kwargs.css_class) $popup.addClass(kwargs.css_class);
//
//   if (kwargs.content) {
//     $popup.find(".popup-content").html(kwargs.content);
//   }
//
//   $body.append($popup);
//
//   if (kwargs.callBack) {
//     kwargs.callBack($popup);
//   }
// }
//
// function hidePopup($popup) {
//   open_popups = openPopupsRemove(open_popups, $popup);
//   if (open_popups.popups.length <= 0) {
//     enableScroll();
//   }
//   $popup.remove();
// }
//
// function openPopupsRemove(open_popups, popup) {
//   let index = 0;
//   while (index !== -1) {
//     index = open_popups.popups.indexOf(popup);
//     if (index !== -1) {
//       open_popups.popups.splice(index, 1);
//       open_popups.callers.splice(index, 1);
//     }
//   }
//   return open_popups;
// }
//
// function disableScroll() {
//   if ($(document).height() > $(window).height()) {
//     let scrollTop = $html.scrollTop() ? $html.scrollTop() : $body.scrollTop(); // Works for Chrome, Firefox, IE...
//     $html.addClass("noscroll").css("top", -scrollTop);
//   }
// }
//
// function enableScroll() {
//   let scrollTop = parseInt($html.css("top"));
//   $html.removeClass("noscroll");
//   $("html,body").scrollTop(-scrollTop);
// }
