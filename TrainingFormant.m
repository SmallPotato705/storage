clear
close all
clc

ampMax = 0.2;
sex = 3;
flg = 2;               % train = 1 / test = 2 
commandAmount = 10;    % Command amount: 1 - 30
commandSample = 9;     % Command sample: 1 - 9
fs = 16000;
TPR =[];
FPR =[];
%% read Database
people = [1,5]; 
[female,male] = ReadDataBase_JY(sex,people,commandAmount);
allPeople = (people(2) - people(1)) + 1;
con =1;
%% Feature Extraction 
for FormantTh = 0.1:0.1:2
    lib_SwitchFilter = [];
        %% Bulid Database
        for i = 1:allPeople
            for j = 1:(commandSample*commandAmount)
                inputFemale = female{j,i};
                inputMale = male{j,i};
                %% Female
                if(isempty(inputFemale))                                           % check audio file
                    femaleSwitchFilter = [];
                else
                    [inputFemale] = noiseReduction_YW(inputFemale,fs, 1, 1, 1);
                    [ F, pos] = vad(inputFemale, fs, 0,0,3,10);
                    if(F >= 2)
                        [ F, ~] = vad(inputFemale, fs, 1,0,3,10,1);
                        fprintf('Female:%d\n',(people(1) + i)-1);
                        fprintf('commandSample:%d\n',floor(j/commandAmount)+1);
                        fprintf('commandAmount:%d\n',(j-(commandAmount*floor(j/commandAmount)))+30);
                        change(con,1)= 'F';
                        change(con,2)=  (people(1) + i)-1;
                        change(con,3)= floor(j/commandAmount)+1;
                        change(con,4)= (j-(commandAmount*floor(j/commandAmount)))+30;
                        con = con + 1 ;
                    end
                    if(F == 0)                                                     % check VAD
                        femaleSwitchFilter = [];
                    else
                        inputFemale = inputFemale(pos(1,1):pos(1,2));
                        outputFemale = scaleAmp_YW(inputFemale, ampMax);
                        femaleSwitchFilter = switchFilter(outputFemale, fs, FormantTh);
                    end
                end
                %% Male
                if(isempty(inputMale))
                    maleSwitchFilter = [];
                else
                    [inputMale] = noiseReduction_YW(inputMale,fs, 1, 1, 1);
                    [ M, pos2] = vad(inputMale, fs, 0,0,3,10);
                    if(M >= 2)
                        [ M, ~] = vad(inputMale, fs, 1,0,3,10,1);
                        fprintf('inputMale:%d\n',(people(1) + i))+1;
                        fprintf('commandSample:%d\n',floor(j/commandAmount)+1);
                        fprintf('commandAmount:%d\n',(j-(commandAmount*floor(j/commandAmount)))+30);
                        change(con,1)= 'M';
                        change(con,2)=  (people(1) + i)+1;
                        change(con,3)= floor(j/commandAmount)+1;
                        change(con,4)= (j-(commandAmount*floor(j/commandAmount)))+30;
                        con = con + 1 ;
                    end
                    if(M == 0)
                        maleSwitchFilter = [];
                    else
                        inputMale = inputMale(pos2(1,1):pos2(1,2));
                        outputMale = scaleAmp_YW(inputMale, ampMax);
                        maleSwitchFilter = switchFilter(outputMale, fs, FormantTh);
                    end
                end

                %% save data
                lib_FemaleSwitchFilter{j,i} = femaleSwitchFilter;
                lib_MaleSwitchFilter{j,i} = maleSwitchFilter;        
            end  
        end
        lib_SwitchFilter = [lib_MaleSwitchFilter lib_FemaleSwitchFilter];
    
    %% Testing 
    DataPeople = size(lib_SwitchFilter,2);
    DataTrain = 6;
    DataTest = 9 - DataTrain;

    DataTrainSample = DataTrain*commandAmount;
    DataAllTrainSample = (DataTrain + DataTest)*commandAmount;
    DataTestSample = DataTest*commandAmount;
    DataFalseTestSample = 9*commandAmount;
    answer = zeros(DataTrainSample,DataPeople);

    for m = 1:DataPeople
        for i = 1:DataTrain
           for j = 1:commandAmount
               answer((i-1)*commandAmount+j,m) = j;
           end
        end
    end
    
    result = zeros(DataTestSample,DataPeople);
    noAudiFile = 0;
    noAudiFile2 = 0;
    %% test
    for i = 1 : DataPeople
        for j = (DataTrainSample+1):DataAllTrainSample
            diffsum_Mfcc = zeros((DataTrainSample),DataPeople);
            %% Database
            if(isempty(lib_SwitchFilter{j,i}))
                result(j - (DataTrainSample),i) = NaN;
                noAudiFile = noAudiFile +1;
            else
                for m =1:DataPeople
                    for k = 1:DataTrainSample 
                        if(isempty(lib_SwitchFilter{k,m}))
                            diffsum_Mfcc(k,m) = NaN;
                        else
                            diff = distDTW(lib_SwitchFilter{j,i},lib_SwitchFilter{k,m});
                            diffsum_Mfcc(k,m) = diff;
                        end
                    end
                end
                [UserminNum,Useridx] = min(diffsum_Mfcc,[],2);
                [NumMinNum,Numidx] = min(UserminNum);
                if(Useridx(Numidx) == i )
                    result(j - (DataTrainSample),i) = answer(Numidx,Useridx(Numidx));
                else
                    result(j - (DataTrainSample),i) = 0;
                end
            end
        end
    end
    [~,indj]=find(result==answer(1:DataTestSample,:));
    all = DataTestSample*DataPeople - noAudiFile;
    tp = length(indj) / all;
    TPR = [TPR tp];
end




