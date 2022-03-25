function onLoadPage(){
   $("#recipe_list").selectize({
     create: true,
     sortField: "text"
   });
}

function getSunday(d) {
  var d = new Date();
  d.setUTCDate(d.getUTCDate() - d.getUTCDay());
  return d.toISOString().slice(0, 10);
}

function recipeRedirect(){
  var recipe_id = document.querySelector("#recipe_list").value;
  console.log(recipe_id);
  if (recipe_id > 0) {
    location.href = "/recipe-site/recipe/" + recipe_id
  }
}

function todaysRecipeRedirect(){
  if (todays_recipe_id != "NONE")
    location.href = "/recipe-site/recipe/" + todays_recipe_id;
}

function scheduleRedirect(){
  var d = new Date();
  var week_begin = getSunday(d);
  location.href = `/recipe-site/recipe-scheduler/?week-start=${week_begin}`;
}
