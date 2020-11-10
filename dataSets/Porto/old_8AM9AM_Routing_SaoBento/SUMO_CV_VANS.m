clear all, close all, clc

A = xlsread('RouteValues8AM9AM.xlsx',6); % Read file

[l c] = find(A(:,35)==2);

WhoIsMissing = linspace(1,length(A),length(A));

NotMissing = ismember(WhoIsMissing',l);

[Index_CV,J] = find(NotMissing==0);

L_Index_VANS = round(0.2*length(Index_CV));
Index_VANS = randsample(Index_CV,L_Index_VANS);

R = A(:,35);

R(Index_VANS,1) = 3;

xlswrite('RouteValues8AM9AM.xlsx',R,6\,'AM2');