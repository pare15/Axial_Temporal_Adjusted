%%% --------------------------------------------
%%% Step 1: Read in .i file (PET Scan 1)
%%% --------------------------------------------
filename = 'post-oposem-t00001-g001.i'; 
dims = [97, 97, 85];      
precision = 'float32';  
byteOrder = 'l';        

fileID = fopen(filename, 'r', byteOrder);
if fileID == -1
    error('PET file not found: %s', filename);
end
petDataVec = fread(fileID, prod(dims), precision);
fclose(fileID); % Close the file

petData = reshape(petDataVec, dims);
disp('Loaded PET Scan 1 (.i file).');

%%% --------------------------------------------
%%% Step 2: Read in DICOM folder (PET Scan 2)
%%% --------------------------------------------
dicomFolder = 'UMI DICHOM';
if ~exist(dicomFolder, 'dir')
    error('DICOM folder not found: %s', dicomFolder);
end

medVol = medicalVolume(dicomFolder);
petDicomMatrix = medVol.Voxels; 
disp('Loaded PET Scan 2 (DICOM folder).');

%%% --------------------------------------------
%%% Step 3: Align PET Scan 1 to PET Scan 2
%%% --------------------------------------------
disp('Aligning scans...');

targetSize = size(petDicomMatrix);
petData_resampled = imresize3(petData, targetSize);

%%% --------------------------------------------
%%% Step 4: Calculate the Difference
%%% --------------------------------------------
disp('Calculating difference matrix...');
differenceMatrix = petDicomMatrix - petData_resampled;

%%% --------------------------------------------
%%% Step 5: Visualize the Difference Heatmap
%%% --------------------------------------------
disp('Displaying difference heatmap...');

% --- THIS IS THE FIX ---
% 1. Find the largest absolute difference
maxAbsVal = max(abs(differenceMatrix(:)));

% 2. Create a symmetric display range (e.g., [-1000, 1000])
% This centers the colormap at 0.
symRange = [-maxAbsVal, maxAbsVal];

% 3. Pass this numeric array to 'DisplayRange'
sliceViewer(differenceMatrix, 'Colormap', jet, 'DisplayRange', symRange);
