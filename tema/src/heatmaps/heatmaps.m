function r = heatmaps(NET_FILE, ROU_FILE, TRACI_PORT)
	% clear all
	% close all
	% clc
	% -------------------------------------------------------------------------
	% read trip files
	% -------------------------------------------------------------------------
	% Convert .xml files to .txt, more specifically, the .rou files
	files = dir('*.rou.xml');
	for i = 1:length(files)
	    filename=files(i).name;
	    [pathstr, name, ext] = fileparts(filename);
	    copyfile(filename, fullfile(pathstr, [name '.txt']))
	end
	% -------------------------------------------------------------------------
	% routes baseline
	% routes saobento
	routes_saobento_A3 = 201:1:220;
	routes_saobento_A3 = routes_saobento_A3';
	% routes boavista
	routes_boavista = 223:1:242;
	routes_boavista = routes_boavista';
	% -------------------------------------------------------------------------
	% read trips file .rou
	rou_files = dir('*.rou.txt');
	howmany_rou_files = length(rou_files);
	% rou_repository = {File_Order_No; Hour; Period; Destination; File_Type; File_Group_Number; scenario; solution};
	rou_repository = zeros(length(rou_files),6);
	% Sort files to group them accordingly
	for i = 1:howmany_rou_files
	    rou_filename=rou_files(i).name;
	    [pathstr, rou_name, ext] = fileparts(rou_filename);
	    rou_repository(i,1) = i;
	    % Identify the period associated to each file
	    Hour_sort = regexp(rou_name,'[0-9]','match');
	    
	    Hour_sort = [Hour_sort{1,1} Hour_sort{1,2}];
	    rou_repository(i,2) = str2double(Hour_sort);
	    
	    Period_sort = contains(rou_name,'AM');
	    % Period_code: AM = 1; and PM = 2
	    if Period_sort == 1
		rou_repository(i,3) = 1;
	    else
		rou_repository(i,3) = 2;
	    end
	    
	    scenario_sort = contains(rou_name,'_baseline');
	    % scenario_code: baseline = 1; and optimal = 2
	    if scenario_sort == 1
		rou_repository(i,5) = 1;
		rou_repository(i,6) = 0;
	    else
		rou_repository(i,5) = 2;
		rou_repository(i,6) = str2double(extractBetween(rou_name,'_solution','.rou'));
	    end
	    
	    % Identify files routing destination
	    % Destination code: Boavista = 1; SaoBento = 2; and A3 = 3, if baseline = 0
	    
	    if rou_repository(i,5) == 1
		rou_repository(i,4) = 0; % baseline ---> no specific scenario
	    else
		Dest_sort = contains(rou_name,'Boavista');
		if Dest_sort == 1
		    rou_repository(i,4) = 1;
		else
		    Dest_sort = contains(rou_name,'SaoBento');
		    if Dest_sort == 1
		        rou_repository(i,4) = 2;
		    else
		        rou_repository(i,4) = 3;
		    end
		end
	    end
	end
	% -------------------------------------------------------------------------
	% read results files
	files = dir('*_results.txt');
	howmanyfiles = length(files);
	% repository = {File_Order_No; Hour; Period; Destination; File_Type; File_Group_Number; scenario; solution};
	repository = zeros(length(files),6);
	% Sort files to group them accordingly
	for i = 1:howmanyfiles
	    repository(i,1) = i;
	    filename=files(i).name;
	    [pathstr, name, ext] = fileparts(filename);
	    % Identify the period associated to each file
	    Hour_sort = regexp(name,'[0-9]','match');
	    
	    Hour_sort = [Hour_sort{1,1} Hour_sort{1,2}];
	    repository(i,2) = str2double(Hour_sort);
	    
	    Period_sort = contains(name,'AM');
	    % Period_code: AM = 1; and PM = 2
	    if Period_sort == 1
		repository(i,3) = 1;
	    else
		repository(i,3) = 2;
	    end
	    % Identify files routing destination
	    % Destination code: Boavista = 1; SaoBento = 2; and A3 = 3
	    Dest_sort = contains(name,'Boavista');
	    if Dest_sort == 1
		repository(i,4) = 1;
	    else
		Dest_sort = contains(name,'SaoBento');
		if Dest_sort == 1
		    repository(i,4) = 2;
		else
		    repository(i,4) = 3;
		end
	    end
	    
	    scenario_sort = contains(name,'_baseline');
	    % scenario_code: baseline = 1; and optimal = 2
	    if scenario_sort == 1
		repository(i,5) = 1;
		repository(i,6) = 0;
	    else
		repository(i,5) = 2;
		repository(i,6) = str2double(extractBetween(name,'_solution','_Routing'));
	    end
	end
	% -------------------------------------------------------------------------
	% Develop heatmaps
	% -------------------------------------------------------------------------
	% Setting up the environment
	tracipath = [cd '/traci4matlab'];

	javaaddpath(tracipath)

	import traci.constants

	system(['sumo-gui' ...
	' --xml-validation ' 'never' ...
	' --remote-port ' TRACI_PORT ...
	' --num-clients ' '1' ...
	' --net-file ' NET_FILE ...
	' --route-files ' ROU_FILE ...
	' --gui-settings-file ' 'viewport_heatmaps.xml' ...
	' --vehroute-output ' 'porto_route_data.xml' ...
	' --summary-output ' 'porto_summary_data.xml' ...
	' --fcd-output.geo ' 'true' ...
	' --write-license ' 'true' ...
	' --window-pos ' '0,0' ...
	' --window-size ' '$(xdpyinfo | awk ''/dimensions/{print $2}'' | awk ''{gsub("x", ",")} {print}'')' ...
	' --time-to-teleport ' '-1' ...
	' --start&']);
	% initialize connection matlab/sumo
	[traciVersion,sumoVersion] = traci.init(str2num(TRACI_PORT))
	timer = 0;
	% get environment lanes ID
	lanes = traci.lane.getIDList();
	lanes = char(lanes);
	lanes_edgeID = cell(length(lanes),1);
	for i = 1:length(lanes)
	    A = lanes(i,:) == '_';
	    if sum(A) == 1
		B = find(A == 1);
		lanes_edgeID{i,1} = lanes(i,1:B(1,1)-1);
	    elseif sum(A) == 2
		B = find(A == 1);
		lanes_edgeID{i,1} = lanes(i,1:B(1,2)-1);
	    else
		lanes_edgeID{i,1} = lanes(i,:);
	    end
	end
	lanes_edgeID = char(lanes_edgeID);
	% -------------------------------------------------------------------------
	% Reading files
	for i = 1:howmanyfiles
	    % read results file i
	    results = readtable(files(i).name);
	    % EdgeID = 1; CO2 = 2; NOx = 3; GHG = 8; noise = 10; emissions_indicator = 13; eco_indicator = 14
	    results_edges = table2cell(results(:,1));
	    edges_results = char(results_edges);
	    % set edge edge color according to the evaluating variable
	    % set data percentiles for each variable
	    CO2_results = table2array(results(:,2));
	    n_vehicles = table2array(results(:,15));
	    edge_distance = table2array(results(:,19));
	    
	    co2_gkm = zeros(length(CO2_results),1);
	    for u = 1:length(CO2_results)
		co2_gkm(u,1) = CO2_results(u,1)/(n_vehicles(u,1)*(edge_distance(u,1)/1000));
	    end
	    co2_gkm(isnan(co2_gkm) == 1) = 0;
	    
	    emissions_indicator_results = table2array(results(:,13));
	    eco_indicator_results = table2array(results(:,14));
	    % -------------------------------------------------------------------------
	    % black edges
	    for w = 1:length(lanes_edgeID)
		edge = strtrim(lanes_edgeID(w,:));
		traci.edge.setMaxSpeed(edge,0.50);
	    end
	    % -------------------------------------------------------------------------
	    % set up CO2 g/km per vehicle heatmap
	    CO2_percentiles = [150, 250, 400];
	    for t = 1:length(lanes_edgeID)
		edge = strtrim(lanes_edgeID(t,:));
		for j = 1:length(edges_results)
		    edge_results = strtrim(edges_results(j,:));
		    compare = strcmp(edge, edge_results);
		    if compare == 1
		        if co2_gkm(j,1) < CO2_percentiles(1,1)
		            traci.edge.setMaxSpeed(edge,1.50);
		        elseif co2_gkm(j,1) > CO2_percentiles(1,1) && co2_gkm(j,1) < CO2_percentiles(1,2)
		            traci.edge.setMaxSpeed(edge,2.10);
		        elseif co2_gkm(j,1) > CO2_percentiles(1,2) && co2_gkm(j,1) < CO2_percentiles(1,3)
		            traci.edge.setMaxSpeed(edge,6.40);
		        else
		            traci.edge.setMaxSpeed(edge,8.90);
		        end
		        break
		    end
		end
	    end
	    pause(5)
	    % advance the simulation one step to update edge color
	    timer = timer + 5;
	    traci.simulationStep(timer);
	    % take screenshot to save CO2 g/km per vehicle heatmap
	    CO2_SC = getscreen;
	    imwrite(CO2_SC.cdata,'CO2_heatmap_draft.png')
	    
	    CO2_SC = imread('CO2_heatmap_draft.png');
	    original_dim = size(CO2_SC);
	    
	    % crop top
	    lines_to_crop_top = round((0.23*original_dim(1,1))/2);
	    CO2_SC(1:lines_to_crop_top,:,:) = [];
	    
	    new_dim = size(CO2_SC);
	    % crop bottom
	    lines_to_crop_bottom = round((0.25*new_dim(1,1))/2);
	    CO2_SC(new_dim(1,1)-lines_to_crop_bottom:end,:,:) = [];
	    
	    % crop sides
	    % left
	    cols_to_crop_left = round((0.21*new_dim(1,2))/2);
	    CO2_SC(:,1:cols_to_crop_left,:) = [];
	    
	    new_dim = size(CO2_SC);
	    % right
	    cols_to_crop_right = round((0.21*new_dim(1,2))/2);
	    CO2_SC(:,new_dim(1,2)-cols_to_crop_right:end,:) = [];
	    
	    final_dim = size(CO2_SC);
	    % read scale fig
	    scale = imread('scale_500m.png');
	    scale_dim = size(scale);
	    
	    % read compass card
	    compass = imread('north.png');
	    compass_dim = size(compass);
	    
	    % read label
	    label_co2_gkm = imread('co2_gkm_label.png');
	    label_dim = size(label_co2_gkm);
	    
	    % prepare final image
	    CO2_SC(final_dim(1,1) + 1 - scale_dim(1,1):end,1:scale_dim(1,2),:) = scale;
	    CO2_SC(1:compass_dim(1,1),1:compass_dim(1,2),:) = compass;
	    CO2_SC(1:label_dim(1,1),final_dim(1,2) + 1 - label_dim(1,2):end,:) = label_co2_gkm;
	    
	    % set name accordingly
	    if repository(i,3) == 1
		period = 'AM';
	    else
		period = 'PM';
	    end
	    
	    if repository(i,5) == 1
		scenario = '_baseline';
	    else
		solution_value = num2str(repository(i,6));
		scenario = ['_optimal', '_solution', solution_value];
	    end
	    
	    if repository(i,4) == 1
		HOUR = num2str(repository(i,2),2);
		first_number = HOUR(1);
		second_number = HOUR(2);
		co2gkm_name = [first_number, period, second_number, period, '_co2gkm_heatmap_Boavista', scenario, '.png'];
	    elseif repository(i,4) == 2
		HOUR = num2str(repository(i,2),2);
		first_number = HOUR(1);
		second_number = HOUR(2);
		co2gkm_name = [first_number, period, second_number, period, '_co2gkm_heatmap_SaoBento', scenario, '.png'];
	    else
		HOUR = num2str(repository(i,2),2);
		first_number = HOUR(1);
		second_number = HOUR(2);
		co2gkm_name = [first_number, period, second_number, period, '_co2gkm_heatmap_A3', scenario, '.png'];
	    end
	    co2gkm_name = ['co2', scenario, '.png'];
	    % create .png image
	    imwrite(CO2_SC,co2gkm_name)
	    % -------------------------------------------------------------------------
	    % black edges
	    for w = 1:length(lanes_edgeID)
		edge = strtrim(lanes_edgeID(w,:));
		traci.edge.setMaxSpeed(edge,0.50);
	    end
	    % -------------------------------------------------------------------------
	    % set up emissions indicator heatmap
	    emissions_inidicator_percentiles = [0.00040 0.0007 0.001];
	    for r = 1:length(lanes_edgeID)
		edge = strtrim(lanes_edgeID(r,:));
		for j = 1:length(edges_results)
		    edge_results = strtrim(edges_results(j,:));
		    compare = strcmp(edge, edge_results);
		    if compare == 1
		        if emissions_indicator_results(j,1) < emissions_inidicator_percentiles(1,1)
		            traci.edge.setMaxSpeed(edge,1.50);
		        elseif emissions_indicator_results(j,1) > emissions_inidicator_percentiles(1,1) && emissions_indicator_results(j,1) < emissions_inidicator_percentiles(1,2)
		            traci.edge.setMaxSpeed(edge,2.10);
		        elseif emissions_indicator_results(j,1) > emissions_inidicator_percentiles(1,2) && emissions_indicator_results(j,1) < emissions_inidicator_percentiles(1,3)
		            traci.edge.setMaxSpeed(edge,6.40);
		        else
		            traci.edge.setMaxSpeed(edge,8.90);
		        end
		        break
		    end
		end
	    end
	    % advance the simulation one step to update edge color
	    timer = timer + 5;
	    traci.simulationStep(timer);
	    % take screenshot to save emissions indicator heatmap
	    Emissions_Ind_SC = getscreen;
	    imwrite(Emissions_Ind_SC.cdata,'emissions_indicator_heatmap_draft.png')
	    
	    Emissions_Ind_SC = imread('emissions_indicator_heatmap_draft.png');
	    original_dim = size(Emissions_Ind_SC);
	    
	    % crop top
	    lines_to_crop_top = round((0.23*original_dim(1,1))/2);
	    Emissions_Ind_SC(1:lines_to_crop_top,:,:) = [];
	    
	    new_dim = size(Emissions_Ind_SC);
	    % crop bottom
	    lines_to_crop_bottom = round((0.25*new_dim(1,1))/2);
	    Emissions_Ind_SC(new_dim(1,1)-lines_to_crop_bottom:end,:,:) = [];
	    
	    % crop sides
	    % left
	    cols_to_crop_left = round((0.21*new_dim(1,2))/2);
	    Emissions_Ind_SC(:,1:cols_to_crop_left,:) = [];
	    
	    new_dim = size(Emissions_Ind_SC);
	    % right
	    cols_to_crop_right = round((0.21*new_dim(1,2))/2);
	    Emissions_Ind_SC(:,new_dim(1,2)-cols_to_crop_right:end,:) = [];
	    
	    final_dim = size(Emissions_Ind_SC);
	    % read scale fig
	    scale = imread('scale_500m.png');
	    scale_dim = size(scale);
	    
	    % read compass card
	    compass = imread('north.png');
	    compass_dim = size(compass);
	    
	    % read label
	    label_EI = imread('EI_label.png');
	    label_dim = size(label_EI);
	    
	    % prepare final image
	    Emissions_Ind_SC(final_dim(1,1) + 1 - scale_dim(1,1):end,1:scale_dim(1,2),:) = scale;
	    Emissions_Ind_SC(1:compass_dim(1,1),1:compass_dim(1,2),:) = compass;
	    Emissions_Ind_SC(1:label_dim(1,1),final_dim(1,2) + 1 - label_dim(1,2):end,:) = label_EI;
	    
	    % set name accordingly
	    if repository(i,4) == 1
		HOUR = num2str(repository(i,2),2);
		first_number = HOUR(1);
		second_number = HOUR(2);
		emissions_indicator_name = [first_number, period, second_number, period, '_emissions_indicator_heatmap_Boavista', scenario, '.png'];
	    elseif repository(i,4) == 2
		HOUR = num2str(repository(i,2),2);
		first_number = HOUR(1);
		second_number = HOUR(2);
		emissions_indicator_name = [first_number, period, second_number, period, '_emissions_indicator_heatmap_SaoBento', scenario, '.png'];
	    else
		HOUR = num2str(repository(i,2),2);
		first_number = HOUR(1);
		second_number = HOUR(2);
		emissions_indicator_name = [first_number, period, second_number, period, '_emissions_indicator_heatmap_A3', scenario, '.png'];
	    end
	    emissions_indicator_name = ['emissions_indicator', scenario, '.png'];
	    % create .png image
	    imwrite(Emissions_Ind_SC,emissions_indicator_name)
	    % -------------------------------------------------------------------------
	    % black edges
	    for w = 1:length(lanes_edgeID)
		edge = strtrim(lanes_edgeID(w,:));
		traci.edge.setMaxSpeed(edge,0.50);
	    end
	    % -------------------------------------------------------------------------
	    % set up eco_indicator heatmap
	    eco_inidicator_percentiles = [0.01 0.06 0.2];
	    for u = 1:length(lanes_edgeID)
		edge = strtrim(lanes_edgeID(u,:));
		for j = 1:length(edges_results)
		    edge_results = strtrim(edges_results(j,:));
		    compare = strcmp(edge, edge_results);
		    if compare == 1
		        if eco_indicator_results(j,1) < emissions_inidicator_percentiles(1,1)
		            traci.edge.setMaxSpeed(edge,1.50);
		        elseif eco_indicator_results(j,1) > CO2_percentiles(1,1) && eco_indicator_results(j,1) < CO2_percentiles(1,2)
		            traci.edge.setMaxSpeed(edge,2.10);
		        elseif eco_indicator_results(j,1) > CO2_percentiles(1,2) && eco_indicator_results(j,1) < CO2_percentiles(1,3)
		            traci.edge.setMaxSpeed(edge,6.40);
		        else
		            traci.edge.setMaxSpeed(edge,8.90);
		        end
		        break
		    end
		end
	    end
	    % advance the simulation one step to update edge color
	    timer = timer + 5;
	    traci.simulationStep(timer);
	    % take screenshot to save eco_indicator heatmap
	    eco_indicator_SC = getscreen;
	    imwrite(eco_indicator_SC.cdata,'eco_indicator_heatmap_draft.png')
	    
	    eco_indicator_SC = imread('eco_indicator_heatmap_draft.png');
	    original_dim = size(eco_indicator_SC);
	    
	    % crop top
	    lines_to_crop_top = round((0.23*original_dim(1,1))/2);
	    eco_indicator_SC(1:lines_to_crop_top,:,:) = [];
	    
	    new_dim = size(eco_indicator_SC);
	    % crop bottom
	    lines_to_crop_bottom = round((0.25*new_dim(1,1))/2);
	    eco_indicator_SC(new_dim(1,1)-lines_to_crop_bottom:end,:,:) = [];
	    
	    % crop sides
	    % left
	    cols_to_crop_left = round((0.21*new_dim(1,2))/2);
	    eco_indicator_SC(:,1:cols_to_crop_left,:) = [];
	    
	    new_dim = size(eco_indicator_SC);
	    % right
	    cols_to_crop_right = round((0.21*new_dim(1,2))/2);
	    eco_indicator_SC(:,new_dim(1,2)-cols_to_crop_right:end,:) = [];
	    
	    final_dim = size(eco_indicator_SC);
	    % read scale fig
	    scale = imread('scale_500m.png');
	    scale_dim = size(scale);
	    
	    % read compass card
	    compass = imread('north.png');
	    compass_dim = size(compass);
	    
	    % read label
	    label_eco_indicator = imread('eco_ind_label.png');
	    label_dim = size(label_eco_indicator);
	    
	    % prepare final image
	    eco_indicator_SC(final_dim(1,1) + 1 - scale_dim(1,1):end,1:scale_dim(1,2),:) = scale;
	    eco_indicator_SC(1:compass_dim(1,1),1:compass_dim(1,2),:) = compass;
	    eco_indicator_SC(1:label_dim(1,1),final_dim(1,2) + 1 - label_dim(1,2):end,:) = label_eco_indicator;
	    
	    % set name accordingly
	    if repository(i,4) == 1
		HOUR = num2str(repository(i,2),2);
		first_number = HOUR(1);
		second_number = HOUR(2);
		eco_indicator_name = [first_number, period, second_number, period, '_eco_indicator_heatmap_Boavista', scenario, '.png'];
	    elseif repository(i,4) == 2
		HOUR = num2str(repository(i,2),2);
		first_number = HOUR(1);
		second_number = HOUR(2);
		eco_indicator_name = [first_number, period, second_number, period, '_eco_indicator_heatmap_SaoBento', scenario, '.png'];
	    else
		HOUR = num2str(repository(i,2),2);
		first_number = HOUR(1);
		second_number = HOUR(2);
		eco_indicator_name = [first_number, period, second_number, period, '_eco_indicator_heatmap_A3', scenario, '.png'];
	    end
	    eco_indicator_name = ['eco_indicator', scenario, '.png'];
	    % create .png image
	    imwrite(eco_indicator_SC,eco_indicator_name)
	    % -------------------------------------------------------------------------
	    % detect edges to return the baseline heatmap per route evaluation
	    %     f = fopen('Trips8AM9AM.rou.txt');
	    for t = 1:howmany_rou_files
		if rou_repository(t,5) == 1 && rou_repository(t,2) == repository(i,2) && rou_repository(t,3) == repository(i,3)
		    %             f = fopen(rou_baseline);
		    f = fopen(rou_files(t).name);
		    trips_txt = textscan(f,'%q','delimiter','<');
		    trips_txt = trips_txt{1,1};
		    
		    if repository(i,4) == 1
		        routes_id = routes_boavista;
		    else
		        routes_id = routes_saobento_A3;
		    end
		    
		    routes = cell(20,3);
		    for k = 1:length(routes_id)
		        for h = 1:length(trips_txt)
		            routes_find = contains(trips_txt{h,1},'" id="route_');
		            if routes_find == 1
		                trips_route_num = extractBetween(trips_txt{h,1},'" id="route_','"/>');
		                route_verify = strcmp(trips_route_num{1,1},num2str(routes_id(k,1)));
		                %             route_number = contains(trips_txt{i,1},num2str(routes_boavista(k,1)));
		                if route_verify == 1
		                    routes{k,1} = routes_id(k,1);
		                    routes{k,2} = extractBetween(trips_txt{h,1},'route edges="','" color="');
		                    routes{k,2} = char(routes{k,2});
		                    routes{k,3} = (strsplit(routes{k,2}, ' '))';
		                end
		            end
		        end
		    end
		    routes_edges_raw = routes{1,3};
		    for d = 2:length(routes)
		        routes_edges_raw = [routes_edges_raw; routes{d,3}];
		    end
		    routes_edges_raw = char(routes_edges_raw);
		    routes_edges = unique(routes_edges_raw, 'rows');
		    % -------------------------------------------------------------------------
		    % black edges
		    for w = 1:length(lanes_edgeID)
		        edge = strtrim(lanes_edgeID(w,:));
		        traci.edge.setMaxSpeed(edge,0.50);
		    end
		    % -------------------------------------------------------------------------
		    % set up CO2 heatmap per route (baseline)
		    for w = 1:length(lanes_edgeID)
		        edge = strtrim(lanes_edgeID(w,:));
		        for e = 1:length(edges_results)
		            edge_results = strtrim(edges_results(e,:));
		            compare = strcmp(edge, edge_results);
		            if compare == 1
		                for v = 1:length(routes_edges)
		                    compare_2 = strcmp(edge, strtrim(routes_edges(v,:)));
		                    if compare_2 == 1
		                        if co2_gkm(e,1) < CO2_percentiles(1,1)
		                            traci.edge.setMaxSpeed(edge,1.50);
		                        elseif co2_gkm(e,1) > CO2_percentiles(1,1) && co2_gkm(e,1) < CO2_percentiles(1,2)
		                            traci.edge.setMaxSpeed(edge,2.10);
		                        elseif co2_gkm(e,1) > CO2_percentiles(1,2) && co2_gkm(e,1) < CO2_percentiles(1,3)
		                            traci.edge.setMaxSpeed(edge,6.40);
		                        else
		                            traci.edge.setMaxSpeed(edge,8.90);
		                        end
		                        break
		                    end
		                end
		            end
		        end
		    end
		    % advance the simulation one step to update edge color
		    timer = timer + 5;
		    traci.simulationStep(timer);
		    % take screenshot to save CO2 g/km per vehicle heatmap
		    CO2_SC = getscreen;
		    imwrite(CO2_SC.cdata,'CO2_heatmap_baseline_routes_draft.png')
		    
		    CO2_SC = imread('CO2_heatmap_baseline_routes_draft.png');
		    original_dim = size(CO2_SC);
		    
		    % crop top
		    lines_to_crop_top = round((0.23*original_dim(1,1))/2);
		    CO2_SC(1:lines_to_crop_top,:,:) = [];
		    
		    new_dim = size(CO2_SC);
		    % crop bottom
		    lines_to_crop_bottom = round((0.25*new_dim(1,1))/2);
		    CO2_SC(new_dim(1,1)-lines_to_crop_bottom:end,:,:) = [];
		    
		    % crop sides
		    % left
		    cols_to_crop_left = round((0.21*new_dim(1,2))/2);
		    CO2_SC(:,1:cols_to_crop_left,:) = [];
		    
		    new_dim = size(CO2_SC);
		    % right
		    cols_to_crop_right = round((0.21*new_dim(1,2))/2);
		    CO2_SC(:,new_dim(1,2)-cols_to_crop_right:end,:) = [];
		    
		    final_dim = size(CO2_SC);
		    
		    % read scale fig
		    scale = imread('scale_500m.png');
		    scale_dim = size(scale);
		    
		    % read compass card
		    compass = imread('north.png');
		    compass_dim = size(compass);
		    
		    % read label
		    label_co2_gkm = imread('co2_gkm_label.png');
		    label_dim = size(label_co2_gkm);
		    
		    % prepare final image
		    CO2_SC(final_dim(1,1) + 1 - scale_dim(1,1):end,1:scale_dim(1,2),:) = scale;
		    CO2_SC(1:compass_dim(1,1),1:compass_dim(1,2),:) = compass;
		    CO2_SC(1:label_dim(1,1),final_dim(1,2) + 1 - label_dim(1,2):end,:) = label_co2_gkm;
		    
		    % set name accordingly
		    if repository(i,3) == 1
		        period = 'AM';
		    else
		        period = 'PM';
		    end
		    if repository(i,4) == 1
		        HOUR = num2str(repository(i,2),2);
		        first_number = HOUR(1);
		        second_number = HOUR(2);
		        co2gkm_name = [first_number, period, second_number, period,'_co2gkm_heatmap_Boavista', scenario, '_routes.png'];
		    elseif repository(i,4) == 2
		        HOUR = num2str(repository(i,2),2);
		        first_number = HOUR(1);
		        second_number = HOUR(2);
		        co2gkm_name = [first_number, period, second_number, period, '_co2gkm_heatmap_SaoBento', scenario, '_routes.png'];
		    else
		        HOUR = num2str(repository(i,2),2);
		        first_number = HOUR(1);
		        second_number = HOUR(2);
		        co2gkm_name = [first_number, period, second_number, period, '_co2gkm_heatmap_A3', scenario, '_routes.png'];
		    end
		    co2gkm_name = ['co2', scenario, '_routes.png'];
		    % create .png image
		    imwrite(CO2_SC,co2gkm_name)
		    % -------------------------------------------------------------------------
		    % black edges
		    for w = 1:length(lanes_edgeID)
		        edge = strtrim(lanes_edgeID(w,:));
		        traci.edge.setMaxSpeed(edge,0.50);
		    end
		    % -------------------------------------------------------------------------
		    % set up emissions indicator heatmap per route (baseline)
		    emissions_inidicator_percentiles = [0.00040 0.0007 0.001];
		    for r = 1:length(lanes_edgeID)
		        edge = strtrim(lanes_edgeID(r,:));
		        for j = 1:length(edges_results)
		            edge_results = strtrim(edges_results(j,:));
		            compare = strcmp(edge, edge_results);
		            if compare == 1
		                for v = 1:length(routes_edges)
		                    compare_2 = strcmp(edge, strtrim(routes_edges(v,:)));
		                    if compare_2 == 1
		                        if emissions_indicator_results(j,1) < emissions_inidicator_percentiles(1,1)
		                            traci.edge.setMaxSpeed(edge,1.50);
		                        elseif emissions_indicator_results(j,1) > emissions_inidicator_percentiles(1,1) && emissions_indicator_results(j,1) < emissions_inidicator_percentiles(1,2)
		                            traci.edge.setMaxSpeed(edge,2.10);
		                        elseif emissions_indicator_results(j,1) > emissions_inidicator_percentiles(1,2) && emissions_indicator_results(j,1) < emissions_inidicator_percentiles(1,3)
		                            traci.edge.setMaxSpeed(edge,6.40);
		                        else
		                            traci.edge.setMaxSpeed(edge,8.90);
		                        end
		                        break
		                    end
		                end
		            end
		        end
		    end
		    % advance the simulation one step to update edge color
		    timer = timer + 5;
		    traci.simulationStep(timer);
		    % take screenshot to save emissions indicator heatmap
		    Emissions_Ind_SC = getscreen;
		    imwrite(Emissions_Ind_SC.cdata,'emissions_indicator_heatmap_baseline_routes_draft.png')
		    
		    Emissions_Ind_SC = imread('emissions_indicator_heatmap_baseline_routes_draft.png');
		    original_dim = size(Emissions_Ind_SC);
		    
		    % crop top
		    lines_to_crop_top = round((0.23*original_dim(1,1))/2);
		    Emissions_Ind_SC(1:lines_to_crop_top,:,:) = [];
		    
		    new_dim = size(Emissions_Ind_SC);
		    % crop bottom
		    lines_to_crop_bottom = round((0.25*new_dim(1,1))/2);
		    Emissions_Ind_SC(new_dim(1,1)-lines_to_crop_bottom:end,:,:) = [];
		    
		    % crop sides
		    % left
		    cols_to_crop_left = round((0.21*new_dim(1,2))/2);
		    Emissions_Ind_SC(:,1:cols_to_crop_left,:) = [];
		    
		    new_dim = size(Emissions_Ind_SC);
		    % right
		    cols_to_crop_right = round((0.21*new_dim(1,2))/2);
		    Emissions_Ind_SC(:,new_dim(1,2)-cols_to_crop_right:end,:) = [];
		    
		    final_dim = size(Emissions_Ind_SC);
		    % read scale fig
		    scale = imread('scale_500m.png');
		    scale_dim = size(scale);
		    
		    % read compass card
		    compass = imread('north.png');
		    compass_dim = size(compass);
		    
		    % read label
		    label_EI = imread('EI_label.png');
		    label_dim = size(label_EI);
		    
		    % prepare final image
		    Emissions_Ind_SC(final_dim(1,1) + 1 - scale_dim(1,1):end,1:scale_dim(1,2),:) = scale;
		    Emissions_Ind_SC(1:compass_dim(1,1),1:compass_dim(1,2),:) = compass;
		    Emissions_Ind_SC(1:label_dim(1,1),final_dim(1,2) + 1 - label_dim(1,2):end,:) = label_EI;
		    
		    % set name accordingly
		    if repository(i,4) == 1
		        HOUR = num2str(repository(i,2),2);
		        first_number = HOUR(1);
		        second_number = HOUR(2);
		        emissions_indicator_name = [first_number, period, second_number, period, '_emissions_indicator_heatmap_Boavista', scenario, '_routes.png'];
		    elseif repository(i,4) == 2
		        HOUR = num2str(repository(i,2),2);
		        first_number = HOUR(1);
		        second_number = HOUR(2);
		        emissions_indicator_name = [first_number, period, second_number, period, '_emissions_indicator_heatmap_SaoBento', scenario, '_routes.png'];
		    else
		        HOUR = num2str(repository(i,2),2);
		        first_number = HOUR(1);
		        second_number = HOUR(2);
		        emissions_indicator_name = [first_number, period, second_number, period, '_emissions_indicator_heatmap_A3', scenario, '_routes.png'];
		    end
		    emissions_indicator_name = ['emissions_indicator', scenario, '_routes.png'];
		    % create .png image
		    imwrite(Emissions_Ind_SC,emissions_indicator_name)
		    % -------------------------------------------------------------------------
		    % black edges
		    for w = 1:length(lanes_edgeID)
		        edge = strtrim(lanes_edgeID(w,:));
		        traci.edge.setMaxSpeed(edge,0.50);
		    end
		    % -------------------------------------------------------------------------
		    % set up eco_indicator heatmap per route (baseline)
		    eco_inidicator_percentiles = [0.01 0.06 0.2];
		    for u = 1:length(lanes_edgeID)
		        edge = strtrim(lanes_edgeID(u,:));
		        for j = 1:length(edges_results)
		            edge_results = strtrim(edges_results(j,:));
		            compare = strcmp(edge, edge_results);
		            if compare == 1
		                for v = 1:length(routes_edges)
		                    compare_2 = strcmp(edge, strtrim(routes_edges(v,:)));
		                    if compare_2 == 1
		                        if eco_indicator_results(j,1) < eco_inidicator_percentiles(1,1)
		                            traci.edge.setMaxSpeed(edge,1.50);
		                        elseif eco_indicator_results(j,1) > eco_inidicator_percentiles(1,1) && eco_indicator_results(j,1) < eco_inidicator_percentiles(1,2)
		                            traci.edge.setMaxSpeed(edge,2.10);
		                        elseif eco_indicator_results(j,1) > eco_inidicator_percentiles(1,2) && eco_indicator_results(j,1) < eco_inidicator_percentiles(1,3)
		                            traci.edge.setMaxSpeed(edge,6.40);
		                        else
		                            traci.edge.setMaxSpeed(edge,8.90);
		                        end
		                        break
		                    end
		                end
		            end
		        end
		    end
		    % advance the simulation one step to update edge color
		    timer = timer + 5;
		    traci.simulationStep(timer);
		    % take screenshot to save eco_indicator heatmap
		    eco_indicator_SC = getscreen;
		    imwrite(eco_indicator_SC.cdata,'eco_indicator_heatmap_baseline_routes_draft.png')
		    
		    eco_indicator_SC = imread('eco_indicator_heatmap_baseline_routes_draft.png');
		    original_dim = size(eco_indicator_SC);
		    
		    % crop top
		    lines_to_crop_top = round((0.23*original_dim(1,1))/2);
		    eco_indicator_SC(1:lines_to_crop_top,:,:) = [];
		    
		    new_dim = size(eco_indicator_SC);
		    % crop bottom
		    lines_to_crop_bottom = round((0.25*new_dim(1,1))/2);
		    eco_indicator_SC(new_dim(1,1)-lines_to_crop_bottom:end,:,:) = [];
		    
		    % crop sides
		    % left
		    cols_to_crop_left = round((0.21*new_dim(1,2))/2);
		    eco_indicator_SC(:,1:cols_to_crop_left,:) = [];
		    
		    new_dim = size(eco_indicator_SC);
		    % right
		    cols_to_crop_right = round((0.21*new_dim(1,2))/2);
		    eco_indicator_SC(:,new_dim(1,2)-cols_to_crop_right:end,:) = [];
		    
		    final_dim = size(eco_indicator_SC);
		    % read scale fig
		    scale = imread('scale_500m.png');
		    scale_dim = size(scale);
		    
		    % read compass card
		    compass = imread('north.png');
		    compass_dim = size(compass);
		    
		    % read label
		    label_eco_indicator = imread('eco_ind_label.png');
		    label_dim = size(label_eco_indicator);
		    
		    % prepare final image
		    eco_indicator_SC(final_dim(1,1) + 1 - scale_dim(1,1):end,1:scale_dim(1,2),:) = scale;
		    eco_indicator_SC(1:compass_dim(1,1),1:compass_dim(1,2),:) = compass;
		    eco_indicator_SC(1:label_dim(1,1),final_dim(1,2) + 1 - label_dim(1,2):end,:) = label_eco_indicator;
		    
		    % set name accordingly
		    if repository(i,4) == 1
		        HOUR = num2str(repository(i,2),2);
		        first_number = HOUR(1);
		        second_number = HOUR(2);
		        eco_indicator_name = [first_number, period, second_number, period, '_eco_indicator_heatmap_Boavista', scenario, '_routes.png'];
		    elseif repository(i,4) == 2
		        HOUR = num2str(repository(i,2),2);
		        first_number = HOUR(1);
		        second_number = HOUR(2);
		        eco_indicator_name = [first_number, period, second_number, period, '_eco_indicator_heatmap_SaoBento', scenario, '_routes.png'];
		    else
		        HOUR = num2str(repository(i,2),2);
		        first_number = HOUR(1);
		        second_number = HOUR(2);
		        eco_indicator_name = [first_number, period, second_number, period, '_eco_indicator_heatmap_A3', scenario, '_routes.png'];
		    end
		    eco_indicator_name = ['eco_indicator', scenario, '_routes.png'];
		    % create .png image
		    imwrite(eco_indicator_SC,eco_indicator_name)
		    
		    % -------------------------------------------------------------------------
		elseif rou_repository(t,5) == 2 && rou_repository(t,2) == repository(i,2) && rou_repository(t,3) == repository(i,3)
		    % -------------------------------------------------------------------------
		    % Optimized scenario
		    %             rou_repository_idx = (rou_repository(:,5) == 2) & (rou_repository(:,2) == repository(i,2)) & (rou_repository(:,3) == repository(i,3));
		    %             a = rou_repository(rou_repository_idx, 1);
		    f = fopen(rou_files(t).name);
		    trips_optimal_txt = textscan(f,'%q','delimiter','<');
		    trips_optimal_txt = trips_optimal_txt{1,1};
		    % -------------------------------------------------------------------------
		    % verify optimized routes
		    opt_routes_idx = contains(trips_optimal_txt,'type="Routing_');
		    
		    num_occurrences = sum(sum(opt_routes_idx));
		    opt_routes_db = cell(num_occurrences,1);
		    
		    contador = 0;
		    for l = 1:length(trips_optimal_txt)
		        if opt_routes_idx(l,1) == 1
		            new_str = extractBetween(trips_optimal_txt{l,1},'" route="','" type="Routing_');
		            contador = contador + 1;
		            opt_routes_db{contador,1} = new_str;
		            opt_routes_db{contador,1} = char(opt_routes_db{contador,1});
		        end
		    end
		    % new routes used by the routing vehicles
		    opt_routes = unique(opt_routes_db);
		    % -------------------------------------------------------------------------
		    % read edges associated to each route
		    edges_txt_idx = contains(trips_optimal_txt,'route id="');
		    
		    num_occurrences = sum(sum(edges_txt_idx));
		    rou_edges_db = cell(num_occurrences,3);
		    
		    contador = 0;
		    for l = 1:length(trips_optimal_txt)
		        if edges_txt_idx(l,1) == 1
		            contador = contador + 1;
		            edge_org = extractBetween(trips_optimal_txt{l,1},'route id="','" edges="');
		            rou_edges_db{contador,1} = edge_org;
		            rou_edges_db{contador,1} = char(rou_edges_db{contador,1});
		            
		            new_str = extractBetween(trips_optimal_txt{l,1},'" edges="','"/>');
		            rou_edges_db{contador,2} = new_str;
		            rou_edges_db{contador,2} = char(rou_edges_db{contador,2});
		            rou_edges_db{contador,3} = (strsplit(rou_edges_db{contador,2}, ' '))';
		        end
		    end
		    optimal_routes = cell(length(opt_routes),1);
		    for l = 1:length(opt_routes)
		        for s = 1:length(rou_edges_db)
		            cond = strcmp(opt_routes{l,1}, rou_edges_db{s,1});
		            if cond == 1
		                optimal_routes{l,1} = rou_edges_db{s,3};
		            end
		        end
		    end
		    
		    opt_routes_edges_raw = optimal_routes{1,1};
		    for d = 2:length(optimal_routes)
		        opt_routes_edges_raw = [opt_routes_edges_raw; optimal_routes{d,1}];
		    end
		    opt_routes_edges_raw = char(opt_routes_edges_raw);
		    opt_routes_edges = unique(opt_routes_edges_raw, 'rows');
		    % -------------------------------------------------------------------------
		    % black edges
		    for w = 1:length(lanes_edgeID)
		        edge = strtrim(lanes_edgeID(w,:));
		        traci.edge.setMaxSpeed(edge,0.50);
		    end
		    % -------------------------------------------------------------------------
		    % set up CO2 heatmap per route (optimal)
		    for w = 1:length(lanes_edgeID)
		        edge = strtrim(lanes_edgeID(w,:));
		        for e = 1:length(edges_results)
		            edge_results = strtrim(edges_results(e,:));
		            compare = strcmp(edge, edge_results);
		            if compare == 1
		                for v = 1:length(opt_routes_edges)
		                    compare_2 = strcmp(edge, strtrim(opt_routes_edges(v,:)));
		                    if compare_2 == 1
		                        if co2_gkm(e,1) < CO2_percentiles(1,1)
		                            traci.edge.setMaxSpeed(edge,1.50);
		                        elseif co2_gkm(e,1) > CO2_percentiles(1,1) && co2_gkm(e,1) < CO2_percentiles(1,2)
		                            traci.edge.setMaxSpeed(edge,2.10);
		                        elseif co2_gkm(e,1) > CO2_percentiles(1,2) && co2_gkm(e,1) < CO2_percentiles(1,3)
		                            traci.edge.setMaxSpeed(edge,6.40);
		                        else
		                            traci.edge.setMaxSpeed(edge,8.90);
		                        end
		                        break
		                    end
		                end
		            end
		        end
		    end
		    % advance the simulation one step to update edge color
		    timer = timer + 5;
		    traci.simulationStep(timer);
		    % take screenshot to save CO2 g/km per vehicle heatmap
		    CO2_SC = getscreen;
		    imwrite(CO2_SC.cdata,'CO2_heatmap_optimal_routes_draft.png')
		    
		    CO2_SC = imread('CO2_heatmap_optimal_routes_draft.png');
		    original_dim = size(CO2_SC);
		    
		    % crop top
		    lines_to_crop_top = round((0.23*original_dim(1,1))/2);
		    CO2_SC(1:lines_to_crop_top,:,:) = [];
		    
		    new_dim = size(CO2_SC);
		    % crop bottom
		    lines_to_crop_bottom = round((0.25*new_dim(1,1))/2);
		    CO2_SC(new_dim(1,1)-lines_to_crop_bottom:end,:,:) = [];
		    
		    % crop sides
		    % left
		    cols_to_crop_left = round((0.21*new_dim(1,2))/2);
		    CO2_SC(:,1:cols_to_crop_left,:) = [];
		    
		    new_dim = size(CO2_SC);
		    % right
		    cols_to_crop_right = round((0.21*new_dim(1,2))/2);
		    CO2_SC(:,new_dim(1,2)-cols_to_crop_right:end,:) = [];
		    
		    final_dim = size(CO2_SC);
		    
		    % read scale fig
		    scale = imread('scale_500m.png');
		    scale_dim = size(scale);
		    
		    % read compass card
		    compass = imread('north.png');
		    compass_dim = size(compass);
		    
		    % read label
		    label_co2_gkm = imread('co2_gkm_label.png');
		    label_dim = size(label_co2_gkm);
		    
		    % prepare final image
		    CO2_SC(final_dim(1,1) + 1 - scale_dim(1,1):end,1:scale_dim(1,2),:) = scale;
		    CO2_SC(1:compass_dim(1,1),1:compass_dim(1,2),:) = compass;
		    CO2_SC(1:label_dim(1,1),final_dim(1,2) + 1 - label_dim(1,2):end,:) = label_co2_gkm;
		    
		    % set name accordingly
		    if repository(i,3) == 1
		        period = 'AM';
		    else
		        period = 'PM';
		    end
		    
		    if repository(i,5) == 1
		        scenario = '_baseline';
		    else
		        solution_value = num2str(repository(i,6));
		        scenario = ['_optimal', '_solution', solution_value];
		    end
		    
		    if repository(i,4) == 1
		        HOUR = num2str(repository(i,2),2);
		        first_number = HOUR(1);
		        second_number = HOUR(2);
		        co2gkm_name = [first_number, period, second_number, period, '_co2gkm_heatmap_Boavista', scenario, '.png'];
		    elseif repository(i,4) == 2
		        HOUR = num2str(repository(i,2),2);
		        first_number = HOUR(1);
		        second_number = HOUR(2);
		        co2gkm_name = [first_number, period, second_number, period, '_co2gkm_heatmap_SaoBento', scenario, '.png'];
		    else
		        HOUR = num2str(repository(i,2),2);
		        first_number = HOUR(1);
		        second_number = HOUR(2);
		        co2gkm_name = [first_number, period, second_number, period, '_co2gkm_heatmap_A3', scenario, '.png'];
		    end
		    co2gkm_name = ['co2', scenario, '.png'];
		    % create .png image
		    imwrite(CO2_SC,co2gkm_name)
		    % -------------------------------------------------------------------------
		    % black edges
		    for w = 1:length(lanes_edgeID)
		        edge = strtrim(lanes_edgeID(w,:));
		        traci.edge.setMaxSpeed(edge,0.50);
		    end
		    % -------------------------------------------------------------------------
		    % set up emissions indicator heatmap per route (optimal)
		    emissions_inidicator_percentiles = [0.00040 0.0007 0.001];
		    for r = 1:length(lanes_edgeID)
		        edge = strtrim(lanes_edgeID(r,:));
		        for j = 1:length(edges_results)
		            edge_results = strtrim(edges_results(j,:));
		            compare = strcmp(edge, edge_results);
		            if compare == 1
		                for v = 1:length(opt_routes_edges)
		                    compare_2 = strcmp(edge, strtrim(opt_routes_edges(v,:)));
		                    if compare_2 == 1
		                        if emissions_indicator_results(j,1) < emissions_inidicator_percentiles(1,1)
		                            traci.edge.setMaxSpeed(edge,1.50);
		                        elseif emissions_indicator_results(j,1) > emissions_inidicator_percentiles(1,1) && emissions_indicator_results(j,1) < emissions_inidicator_percentiles(1,2)
		                            traci.edge.setMaxSpeed(edge,2.10);
		                        elseif emissions_indicator_results(j,1) > emissions_inidicator_percentiles(1,2) && emissions_indicator_results(j,1) < emissions_inidicator_percentiles(1,3)
		                            traci.edge.setMaxSpeed(edge,6.40);
		                        else
		                            traci.edge.setMaxSpeed(edge,8.90);
		                        end
		                        break
		                    end
		                end
		            end
		        end
		    end
		    % advance the simulation one step to update edge color
		    timer = timer + 5;
		    traci.simulationStep(timer);
		    % take screenshot to save emissions indicator heatmap
		    Emissions_Ind_SC = getscreen;
		    imwrite(Emissions_Ind_SC.cdata,'emissions_indicator_heatmap_optimal_routes_draft.png')
		    
		    Emissions_Ind_SC = imread('emissions_indicator_heatmap_optimal_routes_draft.png');
		    original_dim = size(Emissions_Ind_SC);
		    
		    % crop top
		    lines_to_crop_top = round((0.23*original_dim(1,1))/2);
		    Emissions_Ind_SC(1:lines_to_crop_top,:,:) = [];
		    
		    new_dim = size(Emissions_Ind_SC);
		    % crop bottom
		    lines_to_crop_bottom = round((0.25*new_dim(1,1))/2);
		    Emissions_Ind_SC(new_dim(1,1)-lines_to_crop_bottom:end,:,:) = [];
		    
		    % crop sides
		    % left
		    cols_to_crop_left = round((0.21*new_dim(1,2))/2);
		    Emissions_Ind_SC(:,1:cols_to_crop_left,:) = [];
		    
		    new_dim = size(Emissions_Ind_SC);
		    % right
		    cols_to_crop_right = round((0.21*new_dim(1,2))/2);
		    Emissions_Ind_SC(:,new_dim(1,2)-cols_to_crop_right:end,:) = [];
		    
		    final_dim = size(Emissions_Ind_SC);
		    % read scale fig
		    scale = imread('scale_500m.png');
		    scale_dim = size(scale);
		    
		    % read compass card
		    compass = imread('north.png');
		    compass_dim = size(compass);
		    
		    % read label
		    label_EI = imread('EI_label.png');
		    label_dim = size(label_EI);
		    
		    % prepare final image
		    Emissions_Ind_SC(final_dim(1,1) + 1 - scale_dim(1,1):end,1:scale_dim(1,2),:) = scale;
		    Emissions_Ind_SC(1:compass_dim(1,1),1:compass_dim(1,2),:) = compass;
		    Emissions_Ind_SC(1:label_dim(1,1),final_dim(1,2) + 1 - label_dim(1,2):end,:) = label_EI;
		    
		    % set name accordingly
		    if repository(i,4) == 1
		        HOUR = num2str(repository(i,2),2);
		        first_number = HOUR(1);
		        second_number = HOUR(2);
		        emissions_indicator_name = [first_number, period, second_number, period, '_emissions_indicator_heatmap_Boavista', scenario, '.png'];
		    elseif repository(i,4) == 2
		        HOUR = num2str(repository(i,2),2);
		        first_number = HOUR(1);
		        second_number = HOUR(2);
		        emissions_indicator_name = [first_number, period, second_number, period, '_emissions_indicator_heatmap_SaoBento', scenario, '.png'];
		    else
		        HOUR = num2str(repository(i,2),2);
		        first_number = HOUR(1);
		        second_number = HOUR(2);
		        emissions_indicator_name = [first_number, period, second_number, period, '_emissions_indicator_heatmap_A3', scenario, '.png'];
		    end
		    emissions_indicator_name = ['emissions_indicator', scenario, '.png'];
		    % create .png image
		    imwrite(Emissions_Ind_SC,emissions_indicator_name)
		    % -------------------------------------------------------------------------
		    % black edges
		    for w = 1:length(lanes_edgeID)
		        edge = strtrim(lanes_edgeID(w,:));
		        traci.edge.setMaxSpeed(edge,0.50);
		    end
		    % -------------------------------------------------------------------------
		    % set up eco_indicator heatmap per route (optimal)
		    eco_inidicator_percentiles = [0.01 0.06 0.2];
		    for u = 1:length(lanes_edgeID)
		        edge = strtrim(lanes_edgeID(u,:));
		        for j = 1:length(edges_results)
		            edge_results = strtrim(edges_results(j,:));
		            compare = strcmp(edge, edge_results);
		            if compare == 1
		                for v = 1:length(opt_routes_edges)
		                    compare_2 = strcmp(edge, strtrim(opt_routes_edges(v,:)));
		                    if compare_2 == 1
		                        if eco_indicator_results(j,1) < eco_inidicator_percentiles(1,1)
		                            traci.edge.setMaxSpeed(edge,1.50);
		                        elseif eco_indicator_results(j,1) > eco_inidicator_percentiles(1,1) && eco_indicator_results(j,1) < eco_inidicator_percentiles(1,2)
		                            traci.edge.setMaxSpeed(edge,2.10);
		                        elseif eco_indicator_results(j,1) > eco_inidicator_percentiles(1,2) && eco_indicator_results(j,1) < eco_inidicator_percentiles(1,3)
		                            traci.edge.setMaxSpeed(edge,6.40);
		                        else
		                            traci.edge.setMaxSpeed(edge,8.90);
		                        end
		                        break
		                    end
		                end
		            end
		        end
		    end
		    % advance the simulation one step to update edge color
		    timer = timer + 5;
		    traci.simulationStep(timer);
		    % take screenshot to save eco_indicator heatmap
		    eco_indicator_SC = getscreen;
		    imwrite(eco_indicator_SC.cdata,'eco_indicator_heatmap_optimal_routes_draft.png')
		    
		    eco_indicator_SC = imread('eco_indicator_heatmap_optimal_routes_draft.png');
		    original_dim = size(eco_indicator_SC);
		    
		    % crop top
		    lines_to_crop_top = round((0.23*original_dim(1,1))/2);
		    eco_indicator_SC(1:lines_to_crop_top,:,:) = [];
		    
		    new_dim = size(eco_indicator_SC);
		    % crop bottom
		    lines_to_crop_bottom = round((0.25*new_dim(1,1))/2);
		    eco_indicator_SC(new_dim(1,1)-lines_to_crop_bottom:end,:,:) = [];
		    
		    % crop sides
		    % left
		    cols_to_crop_left = round((0.21*new_dim(1,2))/2);
		    eco_indicator_SC(:,1:cols_to_crop_left,:) = [];
		    
		    new_dim = size(eco_indicator_SC);
		    % right
		    cols_to_crop_right = round((0.21*new_dim(1,2))/2);
		    eco_indicator_SC(:,new_dim(1,2)-cols_to_crop_right:end,:) = [];
		    
		    final_dim = size(eco_indicator_SC);
		    % read scale fig
		    scale = imread('scale_500m.png');
		    scale_dim = size(scale);
		    
		    % read compass card
		    compass = imread('north.png');
		    compass_dim = size(compass);
		    
		    % read label
		    label_eco_indicator = imread('eco_ind_label.png');
		    label_dim = size(label_eco_indicator);
		    
		    % prepare final image
		    eco_indicator_SC(final_dim(1,1) + 1 - scale_dim(1,1):end,1:scale_dim(1,2),:) = scale;
		    eco_indicator_SC(1:compass_dim(1,1),1:compass_dim(1,2),:) = compass;
		    eco_indicator_SC(1:label_dim(1,1),final_dim(1,2) + 1 - label_dim(1,2):end,:) = label_eco_indicator;
		    
		    % set name accordingly
		    if repository(i,4) == 1
		        HOUR = num2str(repository(i,2),2);
		        first_number = HOUR(1);
		        second_number = HOUR(2);
		        eco_indicator_name = [first_number, period, second_number, period,'_eco_indicator_heatmap_Boavista', scenario, '.png'];
		    elseif repository(i,4) == 2
		        HOUR = num2str(repository(i,2),2);
		        first_number = HOUR(1);
		        second_number = HOUR(2);
		        eco_indicator_name = [first_number, period, second_number, period, '_eco_indicator_heatmap_SaoBento', scenario, '.png'];
		    else
		        HOUR = num2str(repository(i,2),2);
		        first_number = HOUR(1);
		        second_number = HOUR(2);
		        eco_indicator_name = [first_number, period, second_number, period, '_eco_indicator_heatmap_A3', scenario, '.png'];
		    end
		    eco_indicator_name = ['eco_indicator', scenario, '.png'];
		    % create .png image
		    imwrite(eco_indicator_SC,eco_indicator_name)
		end
	    end
	end
	% delete draft .png files
	files = dir('*_draft.png');
	for i = 1:length(files)
	    filename=files(i).name;
	    [pathstr, name, ext] = fileparts(filename);
	    delete(filename);
	end
	% close connection matlab/sumo
	traci.close()
end
