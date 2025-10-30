
disp('Starting manual import...');

%1. Define dims, voxel size, data type and order from .hdr
dims = [129, 129, 84];
voxel_size = [2.4, 2.4, 2.855];
data_format = 'float';
byte_order = 'l'; % 'l' = little-endian

%2. Open the image file
fid = fopen('HoffmanLarge.i', 'r', byte_order);

%3. Read the raw data
img_data = fread(fid, prod(dims), data_format);
fclose(fid);


%4. Reshape the data into a 3D volume
img_data = reshape(img_data, dims);
%5. Create a spatial referencing object
geom = medicalref3d(dims, voxel_size);

%6. Create the medicalVolume object
medVol = medicalVolume(img_data, geom);

%7. Write the object to a NIfTI file

write(medVol, 'HoffmanLarge1.nii');

disp('SUCCESS: Successfully created .nii file!');
