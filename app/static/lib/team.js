var tooltip = d3.select("body").append("div")
    .attr("id", "tooltip")
    .attr("class", "tooltip")
    .style("opacity", 0);


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
        .style("left", d3.event.pageX + "px")
        .style("top", (d3.event.pageY - 25) + "px");
    tooltip.transition().duration(100).style("opacity", 1);
}


function pathMouseOut(d) {
    tooltip.transition().duration(300).style("opacity", 0);
}


function load_vis(year, class_id) {
    json_url = "../data-vis/?year=" + year + "&team_id=" + team_id + "&class_name=" + class_id;
    
    d3.json(json_url, function(error, data) {
        if(error) load_err(error);

        margin = 20;
        width = Math.min(640, window.innerWidth) - 2 * margin; 
        height = Math.min(480, window.innerHeight) - 2 * margin;
        
        minDim = Math.min(width, height);
        vbWidth = width + 2 * margin;
        vbHeight = height + 2 * margin;
        
        var parseTime = d3.timeParse("%m/%d/%Y");
        data.forEach(function(d) {
            d.date = parseTime(d.date);
            d.points = +d.points;
        });
        
        data.sort(function(a, b) {
            return d3.ascending(a.date, b.date);
        });

        var dataNest = d3.nest()
            .key(function(d) { return d.name; })
            .entries(data);
        
        var line = d3.line()
            .x(function(d) { return x_scale(d.date); })
            .y(function(d) { return y_scale(d.points); });

        var rainbow = d3.interpolateRainbow;

        var total = d3.keys(dataNest).length;
        var rainbowMap = {}
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

        var x_scale = d3.scaleTime().range([margin, width]);
        var y_scale = d3.scaleLinear().range([height, margin]);
        
        x_scale.domain(d3.extent(data, function(d) { return d.date; }));
        y_scale.domain([0, d3.max(data, function(d) { return d.points; })]);

        var x_axis = d3.axisBottom(x_scale);
        var y_axis = d3.axisLeft(y_scale);

        svg.append("g")
            .attr("class", "x axis")
            .attr("transform", "translate(0," + (height - margin) + ")")
            .call(x_axis);
        
        svg.append("g")
            .attr("class", "y axis")
            .attr("transform", "translate(" + margin + ",0)")
            .call(y_axis);

        dataNest.forEach(function(d) {

            var path = svg.append("path")
                .attr("class", "line")
                .attr("fill", "none")
                .attr("id", d.key)
                .attr("stroke", rainbow(rainbowMap[d.key]))
                .attr("stroke-width", 2)
                .attr("d", line(d.values))
                .on("mouseover", pathMouseOver)
                .on("mouseout", pathMouseOut);

            svg.selectAll("circle")
                .data(d.values)
                .enter().append("circle")
                .attr("r", 3)
                .attr("fill", rainbow(rainbowMap[d.key]))
                .attr("stroke", rainbow(rainbowMap[d.key]))
                .attr("stroke-width", 2)
                .attr("cx", function(d) { console.log(d.name + " " + d.date + " " + d.points); return x_scale(d.date); })
                .attr("cy", function(d) { return y_scale(d.points); })
                .on("mouseover", pathMouseOver)
                .on("mouseout", pathMouseOut);
        });
    });
}

window.onload = function() {
    document.getElementById("yearDropDown").dispatchEvent(new Event("change"));
}
