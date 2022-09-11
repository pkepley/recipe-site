var nRecipeRows = 1;
const weekDays = ["Sunday", "Monday", "Tuesday", "Wednesday",
                  "Thursday", "Friday", "Saturday"];

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

function populateSelect(i) {
  const selId = `recipe-select-${weekDays[i]}`;
  const sel = document.getElementById(selId);

  var opt = document.createElement("option");
  opt.setAttribute("selected", "true");
  opt.setAttribute("value", "");
  opt.setAttribute("disabled", "");
  opt.text = "-- select an option --";
  sel.add(opt);

  $("#" + selId).selectize({
    create: false,
    searchField: "recipe_name",
    labelField:  "recipe_name",
    sortField:   "recipe_name",
    valueField:  "recipe_id",
    maxItems: 1,
    closeAfterSelect: true,
    render: {
      option: function (item, escape) {
        return (
         "<div>" +
         "<span>" + item.recipe_name + "</span>" +
         "</div>"
        );
      },
    },
    load: function (query, callback) {
      if (!query.length) return callback();
      $.ajax({
        url: "../recipe-search?search-terms=" + encodeURIComponent(query),
        type: "GET",
        error: function () {
          callback();
        },
        success: function (res) {
          console.log(res)
          callback(res);
        },
      });
    },
    onChange: function(value){
      if (value != "") {
        enableCount(i);
      } else{
        disableCount(i);
      }
    },
  });
}

function dePopulateSelect(i) {
  const selId = `recipe-select-${weekDays[i]}`;
  var $select = $('#' + selId).selectize();
  var control = $select[0].selectize;
  control.setValue(0, false);
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

function getThisSunday(d) {
  var d = new Date();
  d.setUTCDate(d.getUTCDate() - d.getUTCDay());
  return d.toISOString().slice(0, 10);
}

function setWeekStart(weekStartString) {
  document.getElementById('week-start').textContent = weekStartString;
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

function filterGroceryList(weekDaysScheduled, recipeIds, recipeCounts) {
  let idx_keep = new Array();

  for (let i = 0; i < weekDaysScheduled.length; i++) {
    if (recipeIds[i] || (recipeCounts[i] != 0)) {
      idx_keep.push(i);
    }
  }

  return {
    "weekdays-scheduled": idx_keep.map(i => weekDaysScheduled[i]),
    "recipe-ids": idx_keep.map(i => recipeIds[i]),
    "recipe-counts": idx_keep.map(i => recipeCounts[i])
  }
}

function setGroceryList(weekStart, weekDaysScheduled, recipeIds, recipeCounts) {
  var gl = filterGroceryList(weekDaysScheduled, recipeIds, recipeCounts);

  var newUrl = "/recipe-site/recipe-scheduler/create-schedule?";
  newUrl = newUrl + "week-start=" + weekStart;
  newUrl = newUrl + "&weekdays-scheduled=" + gl["weekdays-scheduled"].join(",");
  newUrl = newUrl + "&recipe-ids=" + gl["recipe-ids"].join(",");
  newUrl = newUrl + "&recipe-counts=" + gl["recipe-counts"].join(",");
  console.log(newUrl);

  var xhr = new XMLHttpRequest();
  xhr.open("POST", newUrl, false);
  xhr.send();

  console.log(xhr)

  return xhr;
}

function getGroceryList() {
  var weekStart    = getWeekStart();
  var newUrl = "/recipe-site/recipes-scheduled?week-start=" + weekStart;

  return $.getJSON(newUrl).then(function(data) {
    var rslt = {
      day_of_week: [],
      recipe_id: [],
      recipe_name: [],
      quantity: []
    }

    for (const item in data) {
      rslt.day_of_week.push(data[item].day_of_week);
      rslt.recipe_id.push(data[item].recipe_id);
      rslt.recipe_name.push(data[item].recipe_name);
      rslt.quantity.push(data[item].quantity);
    }

    return rslt;
  });
}

function setRecipe(i, recipe_id, recipe_name, recipe_amount) {
  // set recipe
  const selId = `recipe-select-${weekDays[i]}`;
  var $select = $('#' + selId).selectize();
  var control = $select[0].selectize;
  var cntId = `cnt-${weekDays[i]}`;

  // update the selectize - must be done BEFORE updating the amount
  control.clear();
  if (recipe_amount > 0) {
    control.addOption({recipe_id: recipe_id, recipe_name: recipe_name})
    control.setValue(recipe_id, false);
  }

  // set the amount
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
  let recipe_name = (recipe_amount > 0 ) ? control.getItem(control.getValue())[0].innerHTML : 0;

  return {
    recipe_id: control.getValue(),
    recipe_amount: recipe_amount,
    recipe_name: recipe_name
  }
}

function swapRecipes(srcIdx, tgtIdx) {
  const srcRecipeData = getRecipe(srcIdx);
  const tgtRecipeData = getRecipe(tgtIdx);
  setRecipe(tgtIdx, srcRecipeData.recipe_id, srcRecipeData.recipe_name, srcRecipeData.recipe_amount);
  setRecipe(srcIdx, tgtRecipeData.recipe_id, tgtRecipeData.recipe_name, tgtRecipeData.recipe_amount);
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

  //window.location.href = `/recipe-site/recipe-scheduler/?week-start=${weekStart}`;

  document.getElementById("week-start").innerHTML = weekStart;

  updatePage();
}


function workSaved() {
  // current state
  var recipeIds    = getRecipeIds();
  var recipeCounts = getRecipeCounts();
  var weekStart    = getWeekStart();

  var gl_in = filterGroceryList(
    [0,1,2,3,4,5,6],
    recipeIds,
    recipeCounts
  );

  return getGroceryList().then(function(gl_out){
    console.log(gl_in);
    console.log(gl_out);

    rslt_okay = true;
    rslt_okay = rslt_okay & gl_in['weekdays-scheduled'].length == gl_out['day_of_week'].length
    rslt_okay = rslt_okay & gl_in['recipe-counts'].length == gl_out['quantity'].length
    rslt_okay = rslt_okay & gl_in['recipe-ids'].length == gl_out['recipe_id'].length
    rslt_okay = rslt_okay & gl_in["weekdays-scheduled"].every((v,i) => +gl_out["day_of_week"][i] == +v)
    rslt_okay = rslt_okay & gl_in["recipe-counts"].every((v,i) => +gl_out["quantity"][i] == +v)
    rslt_okay = rslt_okay & gl_in["recipe-ids"].every((v,i) => +gl_out["recipe_id"][i] == +v)

    return rslt_okay
  });
}

function saveWork() {
  // current state
  var recipeIds    = getRecipeIds();
  var recipeCounts = getRecipeCounts();
  var weekStart    = getWeekStart();
  console.log(recipeIds)

  var gl_in = filterGroceryList(
    [0,1,2,3,4,5,6],
    recipeIds,
    recipeCounts
  )

  setGroceryList(
    weekStart,
    gl_in["weekdays-scheduled"],
    gl_in["recipe-ids"],
    gl_in["recipe-counts"]
  )

  workSaved().then(function(rslt_okay) {
    if (rslt_okay) {
      displaySnackBar("Save Succeeded", "success");
    } else {
      displaySnackBar("Save Failed", "failure");
    }
  })
}

function displaySnackBar(msgString, showSubClass="") {
  var className = "show";
  if (showSubClass) {
    className = className + showSubClass;
  }
  var snackbar = document.getElementById("snackbar");
  snackbar.className = className;
  snackbar.textContent = msgString;
  setTimeout(function(){ snackbar.className = snackbar.className.replace(className, ""); }, 2000);
}

function modalDo(f) {
  f();
  $('#exampleModal').modal('hide');
}

function modalSaveThenDo(f) {
  saveWork();
  modalDo(f);
}

function modalVerify(f){
  workSaved().then(function(work_saved) {
    if (work_saved) {
      f();
    } else{
      $('#exampleModal').modal('show');
      // TODO: we still aren't verifying that the save worked. We *should*
      // really check this!!!
      document.getElementById("modal-button-save").onclick = () => modalSaveThenDo(f);
      document.getElementById("modal-button-nosave").onclick = () => modalDo(f);
    }
  });
}

function goHome(){
  window.location.href='/recipe-site/';
}


function fetchRecipeList() {
  var newUrl = '/recipe-site/recipe-list.json';

  return $.getJSON(newUrl).then(function(data) {
    return data;
  });
}


function updatePage() {
  getGroceryList().then(function(gl) {
    for(let i = 0; i < 7; i++) {
      dePopulateSelect(i);
      disableCount(i);
    }
    for(let j = 0; j < gl['day_of_week'].length; j++) {
      setRecipe(gl['day_of_week'][j], gl['recipe_id'][j], gl['recipe_name'][j], gl['quantity'][j]);
    }
  })
}

function clearOnZero(i) {
  var cnt = document.getElementById(`cnt-${weekDays[i]}`).value;
  if (cnt == 0) {
    dePopulateSelect(i);
  }
}

function onLoadPage() {

  setWeekStart(getThisSunday());

  //fetchRecipeList().then(function(recipe_list) {
    // populate each selectize
    for (let i = 0; i < 7; i++) {
      populateSelect(i);//, recipe_list);
      disableCount(i);

      // add an event listener to clear the recipe if zero are requested
      document.getElementById(`cnt-${weekDays[i]}`).onchange = () => clearOnZero(i);
    }

    // pull in
    updatePage();
  //})

}
