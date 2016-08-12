var tooltip = d3.select("body").append("div")
    .attr("id", "tooltip")
    .attr("class", "tooltip")
    .style("width", "auto")
    .style("background", "lightgrey")
    .style("padding", "3px")
    .style("padding-left", "5px")
    .style("padding-right", "5px")
    .style("border-radius", "5px")
    .style("opacity", 0);

var rainbowMap = {}
var rainbowRGB = {}

function load_err(err) {
    throw err;
}


function debug_obj(obj) {
    var propVal;
    for(var propName in obj) {
        propValue = obj[propName];
        console.log(propName, propValue);
    }
}


function reset_data_vis() {
    d3.select(".data-vis").selectAll("*").remove();
}


function handleTeamYearChoice(year) {
    reset_data_vis();
    initClassMenu(year);
    load_vis(year, get_class());
}


function handleClassChoice(class_id) {
    reset_data_vis();
    load_vis(get_year(), class_id);
}


function initClassMenu(year) {
    var menu = document.getElementById("classDropDown");
    clearMenu(menu);
    addMenuOptions(menu, data_options[year]);
}


function addMenuOptions(menu, opts) {
    opts.forEach(function(c) {
        option = document.createElement("option");
        option.text = option.value = c;
        menu.appendChild(option);
    });
}


function clearMenu(menu) {
    menu.innerHTML = null;
}


function get_class() {
    return document.getElementById("classDropDown").value;
}


function get_year() {
    return document.getElementById("yearDropDown").value;
}


function pathMouseOver(d) {
    tooltip.html(this.id)
        .style("left", (d3.event.pageX + 5) + "px")
        .style("top", (d3.event.pageY - 35) + "px");
    tooltip.transition().duration(100).style("opacity", 1);
    document.getElementById(this.id + "AHREF").style.background = rainbowRGB[this.id];
}


function pathMouseOut(d) {
    tooltip.transition().duration(300).style("opacity", 0);
    document.getElementById(this.id + "AHREF").style.background = "";
}


function load_vis(year, class_id) {
    json_url = "../data-vis/?year=" + year + "&team_id=" + team_id + "&class_name=" + encodeURIComponent(class_id);
    
    d3.json(json_url, function(error, data) {
        if(error) load_err(error);

        margin = 20;
        width = Math.min(640, window.innerWidth) - 2 * margin; 
        height = Math.min(480, window.innerHeight) - 2 * margin;
        vbWidth = width + 2 * margin;
        vbHeight = height + 2 * margin;
        
        var dateTicks = [];
        
        var parseTime = d3.timeParse("%m/%d/%Y");
        
        data.forEach(function(d) {
            d.date = parseTime(d.date);
            d.total = 0;
        });
        
        data.sort(function(a, b) {
            return d3.ascending(a.date, b.date);
        });

        var dataNest = d3.nest()
            .key(function(d) { return d.name; })
            .entries(data);
        

        dataNest.forEach(function(d) {
            runTotal = 0;
            d.values.forEach(function(vals) {
                runTotal += vals.points;
                vals.total = runTotal;
                if(dateTicks.indexOf(vals.date) < 0) {
                    dateTicks.push(vals.date);
                }
            });
        });
        
        var line = d3.line()
            .x(function(d) { return x_scale(d.date); })
            .y(function(d) { return y_scale(d.total); });

        var rainbow = d3.interpolateRainbow;
        
        var total = d3.keys(dataNest).length;
        
        d3.keys(dataNest).map(function(d) {
            rainbowMap[dataNest[d].key] = d / total;
        });

        var svg = d3.select(".data-vis")
            .append("div")
            .classed("svg-container", true)
            .append("svg")
            .attr("preserveAspectRatio", "xMinYMin meet")
            .attr("viewBox", "0 0 " + vbWidth + " " + vbHeight)
            .attr("transform", "translate(" + margin + "," + margin +")")
            .classed("svg-content-responsive", true);

        var border = svg.append("rect")
            .attr("x", 0)
            .attr("y", 0)
            .attr("height", height+margin)
            .attr("width", width+margin)
            .style("fill", "none")
            .style("stroke", "black")
            .style("stroke-width", "2");

        var x_scale = d3.scaleTime().range([2*margin, width]);
        var y_scale = d3.scaleLinear().range([height-margin, margin]);
        
        minMax = d3.extent(data, function(d) { return d.date; });
        x_scale.domain([minMax[0], minMax[1]])
        y_scale.domain([0, d3.max(data, function(d) { return d.total; })]);

        var x_axis = d3.axisBottom(x_scale)
            .tickFormat(d3.timeFormat("%m-%d"))
            .tickValues(dateTicks);
        var y_axis = d3.axisLeft(y_scale);

        svg.append("g")
            .attr("class", "x axis")
            .attr("transform", "translate(0," + (height - margin) + ")")
            .call(x_axis);
        
        svg.append("g")
            .attr("class", "y axis")
            .attr("transform", "translate(" + (2*margin) + ",0)")
            .call(y_axis);

        svg.append("text")
            .attr("y", margin)
            .attr("x", 6*margin)
            .attr("dy", ".75em")
            .attr("text-anchor", "end")
            .text("Total Points");
        
        svg.append("text")
            .attr("text-anchor", "middle")
            .attr("y", vbHeight - margin - 5)
            .attr("x", width / 2  + margin)
            .text("Race Date");

        dataNest.forEach(function(data) {
            
            var path = svg.append("path")
                .attr("class", "dataLine")
                .attr("fill", "none")
                .attr("id", data.key)
                .attr("stroke", function(d) {
                        color = rainbow(rainbowMap[data.key]);
                        rainbowRGB[data.key] = d3.rgb(color);
                        return color;
                    })
                .attr("stroke-width", 2)
                .attr("d", line(data.values))
                .on("mouseover", pathMouseOver)
                .on("mouseout", pathMouseOut);
            

            svg.selectAll(data.key+"circle")
                .data( function(a1) {  return data.values } )
                .enter().append("circle")
                .attr("class", "dataPoint")
                .attr("id", data.key)
                .attr("r", 2)
                .attr("fill", rainbow(rainbowMap[data.key]))
                .attr("stroke", rainbow(rainbowMap[data.key]))
                .attr("stroke-width", 2)
                .attr("cx", function(d) { return x_scale(d.date); })
                .attr("cy", function(d) { return y_scale(d.total); })
                .on("mouseover", pathMouseOver)
                .on("mouseout", pathMouseOut);
        });
    });
}

window.onload = function() {
    document.getElementById("yearDropDown").dispatchEvent(new Event("change"));
}
