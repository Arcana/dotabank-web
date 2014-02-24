$(function(){
	var dict = {
		"radiant":{text:"Radiant",element:"team"},
		"dire":{text:"Dire",element:"team"},
		"tower":{text:"Tower",element:"type"},
		"barracks":{text:"Barracks",element:"type"},
		"ancient":{text:"Ancient",element:"type"},
		"tier_1":{text:"Tier 1",element:"tier"},
		"tier_2":{text:"Tier 2",element:"tier"},
		"tier_3":{text:"Tier 3",element:"tier"},
		"anc":{text:"Tier 4",element:"tier"},
		"top":{text:"Top",element:"location"},
		"bot":{text:"Bottom",element:"location"},
		"mid":{text:"Middle",element:"location"},
		"ranged":{text:"Ranged",element:"tier"},
		"melee":{text:"Melee",element:"tier"}
	}
	function hoverIn(e){
		$("#hover_box #building_team, #hover_box #building_location, #hover_box #building_tier, #hover_box #building_type").text("");
		$('#hover_box').css({
			left:e.pageX+25,
			top:e.pageY+25
		});
		var class_list = $(this).attr('class').split(/\s+/);
		$.each(class_list, function (key, val) {
			var property = dict[val];
			if (property.element=="team"){
				$("#hover_box #building_team").removeClass().addClass(property.text.toLowerCase());
			}
			$("#hover_box #building_"+property.element).text(property.text);
		});
		$("#hover_box").show();
	}
	function hoverOut() {
		$("#hover_box").hide();
	}
	$(".tower").hover(hoverIn, hoverOut);
	$(".barracks").hover(hoverIn, hoverOut);
	$(".ancient").hover(hoverIn, hoverOut);
});