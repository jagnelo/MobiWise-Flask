% 230 - 0 - 18000
clear all, close all, clc

A = xlsread('RouteValues8AM9AM.xlsx','A:F');
[nl nc] = size(A);
A = round(A(:,5))';

Soma = sum(A);

a = 0;
b = 3600;

R = zeros(Soma,2);
pos = 1;

for i = 1:1:nl
    
    if i == 1
        r = b.*rand(A(1,i),1);
        R(1:A(1,i),2) = r;
        R(1:A(1,i),1) = i;
        
        pos = A(1,i) + pos;
    else
        r = b.*rand(A(1,i),1);
        n = A(1,i) - 1;
        R(pos:pos+n,2) = r;
        R(pos:pos+n,1) = i;
        
        pos = A(1,i) + pos;
    end
end

% r_range = [min(r) max(r)];
R(:,1) = R(:,1)-1;
text = sprintf('I2:J%.f',round(Soma+1,0));
xlswrite('RouteValues.xlsx',R,1,text);
