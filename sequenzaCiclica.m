function output = sequenzaCiclica(input)
    output = zeros(size(input)); % Inizializza il vettore di output con zeri
    
    for i = 1:length(input)
        if mod(input(i), 4) == 1
            output(i) = 0;
        elseif mod(input(i), 4) == 2
            output(i) = 1;
        elseif mod(input(i), 4) == 3
            output(i) = 0;
        elseif mod(input(i), 4) == 0
            output(i) = -1;
        end
    end
end
