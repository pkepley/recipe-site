var nRecipeRows = 1;
const weekDays = ["sun", "mon", "tue", "wed", "thu", "fri", "sat"];

function disableCount(i) {
  const cntId = `cnt-${weekDays[i]}`;
  document.getElementById(cntId).disabled = true;
  document.getElementById(cntId).value    = 0;
}

function enableCount(i) {
  const cntId = `cnt-${weekDays[i]}`;
  document.getElementById(cntId).disabled = false;
  document.getElementById(cntId).value    = 1;
}

function populateSelect(i, options) {
  const selId = `recipe-select-${weekDays[i]}`;
  const sel = document.getElementById(selId);

  var opt = document.createElement("option");
  opt.setAttribute("selected", "true");
  opt.setAttribute("value", "");
  opt.setAttribute("disabled", "");
  opt.text = "-- select an option --";
  sel.add(opt);

  for (var k of Object.keys(options)) {
    var opt = document.createElement("option");
    opt.value = k;
    opt.text = options[k];
    sel.add(opt);
  }

  $("#" + selId).selectize({
    plugins: ["remove_button"],
    //persist: false,
    create: false,
    sortField: "text",
    maxItems: 1,
    closeAfterSelect: true,
    onChange:function(value){
      if (value != "") {
        enableCount(i);
      } else{
        disableCount(i);
      }
    }
  });
}

function getRecipeIds() {
  var recipeIds = [];

  for (var i = 0; i < 7; i++) {
    var selId = `recipe-select-${weekDays[i]}`;
    console.log(selId);
    var recipe = document.getElementById(selId);
    recipeIds.push(recipe.value);
  }

  return recipeIds;
}

function getRecipeCounts() {
  var recipeCounts = [];

  for (var i = 0; i < 7; i++) {
    var cntId = `cnt-${weekDays[i]}`;
    console.log(cntId);
    var amount = document.getElementById(cntId);
    recipeCounts.push(amount.value);
  }

  return recipeCounts;
}

function getWeekStart() {
  return document.getElementById('week-start').textContent;
}

function getGroceryListPrint() {
  var recipeIds = getRecipeIds();
  var recipeCnts = getRecipeCounts();

  var newUrl = "/recipe-site/grocery-list-print/";
  newUrl = newUrl + "?recipe_ids=" + recipeIds.join(",");
  newUrl = newUrl + "&recipe_quantities=" + recipeCnts.join(",");
  document.location.href = newUrl;
}

function setGroceryList() {
  var recipeIds    = getRecipeIds();
  var recipeCounts = getRecipeCounts();
  var weekStart    = getWeekStart();

  var newUrl = "/recipe-site/recipe-scheduler/create-schedule?";
  newUrl = newUrl + "week-start=" + weekStart;
  newUrl = newUrl + "&recipe-ids=" + recipeIds.join(",");
  newUrl = newUrl + "&recipe-counts=" + recipeCounts.join(",");

  console.log(newUrl);
  //document.location.href = newUrl
  var oReq = new XMLHttpRequest();
  oReq.open("POST", newUrl);
  oReq.send();
}

function setRecipe(i, recipe_id, recipe_amount) {
  // set recipe
  const selId = `recipe-select-${weekDays[i]}`;
  var $select = $('#' + selId).selectize();
  var control = $select[0].selectize;
  control.setValue(recipe_id);

  // set amount
  var cntId = `cnt-${weekDays[i]}`;
  document.getElementById(cntId).value = recipe_amount;

}

function getRecipe(i) {
  // recipe_id
  const selId = `recipe-select-${weekDays[i]}`;
  const $select = $('#' + selId).selectize();
  const control = $select[0].selectize;

  // recipe_amount
  const cntId = `cnt-${weekDays[i]}`;
  const recipe_amount = document.getElementById(cntId).value;

  return {
    recipe_id: control.getValue(),
    recipe_amount: recipe_amount
  }
}

function swapRecipes(srcIdx, tgtIdx) {
  const srcRecipeData = getRecipe(srcIdx);
  const tgtRecipeData = getRecipe(tgtIdx);
  setRecipe(tgtIdx, srcRecipeData.recipe_id, srcRecipeData.recipe_amount);
  setRecipe(srcIdx, tgtRecipeData.recipe_id, tgtRecipeData.recipe_amount);
}

function moveUp(srcDay) {
  if (srcDay != "sun"){
    const srcIdx = weekDays.indexOf(srcDay)
    const tgtIdx = srcIdx - 1;
    const tgtDay = weekDays[tgtIdx];
    swapRecipes(srcIdx, tgtIdx);
  }
}

function moveDown(srcDay) {
  if (srcDay != "sat"){
    const srcIdx = weekDays.indexOf(srcDay)
    const tgtIdx = srcIdx + 1;
    const tgtDay = weekDays[tgtIdx];
    swapRecipes(srcIdx, tgtIdx);
  }
}

function changeWeek(n_weeks_change) {
  var weekStart = new Date(getWeekStart());

  weekStart.setUTCDate(weekStart.getUTCDate() + n_weeks_change * 7);

  weekStart = weekStart.toISOString().slice(0, 10);

  window.location.href = `/recipe-site/recipe-scheduler/?week-start=${weekStart}`;
  //"window.location.href='/recipe-site/'"
}

function onLoadPage() {
  for (var i = 0; i < 7; i++) {
    populateSelect(i, recipe_list);
  }

  for (var i = 0; i < 7; i++) {
    disableCount(i);
  }

  for (var i = 0; i < scheduled_recipe_names.length; i++ ){
    setRecipe(scheduled_day_of_week[i], scheduled_recipe_ids[i], scheduled_quantities[i]);
  }
}
