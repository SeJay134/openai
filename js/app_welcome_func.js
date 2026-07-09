/* =========================
   DOM ELEMENTS
========================= */

const welcomeText =
  document.getElementById("app_welcome"); // welcomeText

const chatInput =
  document.getElementById("input"); // chatInput

/* =========================
   text welcome
========================= */

const titleText =
  "Hello! I’m iishka from Irishki, ai assistant." 

app_welcome.textContent =
  titleText;

/* =========================
   smooth show
========================= */

window.addEventListener("load", () => {

  setTimeout(() => {

    app_welcome.classList.add("show");

  }, 200);

});

/* =========================
   disappear on focus
========================= */

input.addEventListener("focus", () => {

  app_welcome.classList.remove("show");

  app_welcome.classList.add("hide");

});