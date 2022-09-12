var recipeRowIds = new Set();
var totalRecipeCnts = 0;

function populateSelect(selId) {
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
          "<div style='margin-bottom: 5px;'>" +
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

function getNewId() {
  const idTimePart = (new Date()).getTime();
  const idRandPart = Math.floor(10000000 * Math.random() / 2);
  const id = (idTimePart + idRandPart).toString(16).slice(2);

  return id;
}


function addTableRow(tableId, options) {
  const tbl = document.getElementById(tableId);

  // add me to the list
  const id = getNewId();
  recipeRowIds.add(id);

  // the new row
  var row = document.createElement("tr");
  row.id = `recipe-row-${id}`;
  tbl.appendChild(row);

  // delete me
  var delCell = document.createElement("td");
  row.appendChild(delCell);

  // the selector cell
  var selCell = document.createElement("td");
  row.appendChild(selCell);

  // the count cell
  var cntCell = document.createElement("td");
  row.appendChild(cntCell);

  // the delete
  var del = document.createElement("button");
  del.setAttribute('class', "btn btn-primary");
  del.innerHTML = "<i class=\"bi bi-dash-square\"></i>";
  del.setAttribute('onclick', `minusRow('${id}')`);
  delCell.appendChild(del);

  // the recipe selection drop down
  var sel = document.createElement("select");
  var selId = `recipe-select-${id}`;
  sel.setAttribute('id', selId);
  selCell.appendChild(sel);
  populateSelect(selId);

  // the recipe count drop down
  var cnt = document.createElement("input");
  var cntId = `recipe-count-${id}`;
  cnt.setAttribute('id', cntId);
  cnt.setAttribute('value', 1);
  cnt.setAttribute('type', 'number');
  cnt.setAttribute('min', 1);
  cnt.setAttribute('class', "form-control");

  //cnt.value = 1;
  //cnt.type = "number"
  //cnt.min = 1;
  //cnt.setAttribute('class', "form-control");
  cntCell.appendChild(cnt);
}

function plusRow() {
  addTableRow("recipe-table-body", []);
}

function minusRow(rowId) {
  if (recipeRowIds.size > 1) {
    var row = document.getElementById(`recipe-row-${rowId}`);
    row.remove();
    recipeRowIds.delete(rowId);
  }
}

function getRecipeIds() {
  var recipeIds = [];

  for (const rowId of recipeRowIds) {
    var selId = `recipe-select-${rowId}`;
    var recipe = document.getElementById(selId);
    recipeIds.push(recipe.value);
  }

  return recipeIds;
}

function getRecipeCounts() {
  var recipeCnts = [];
  for (const id of recipeRowIds) {
    var selId = `recipe-count-${id}`;
    var recipe = document.getElementById(selId);
    recipeCnts.push(recipe.value);
  }

  return recipeCnts;
}

function getGroceryListPrint() {
  var recipeIds = getRecipeIds();
  var recipeCnts = getRecipeCounts();

  var newUrl = "/recipe-site/grocery-list-print/";
  newUrl = newUrl + "?recipe_ids=" + recipeIds.join(",");
  newUrl = newUrl + "&recipe_quantities=" + recipeCnts.join(",");
  document.location.href = newUrl;
}

function onLoadPage() {
  addTableRow("recipe-table-body", []);//, recipe_list);
}
