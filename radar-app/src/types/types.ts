export interface PrecipitationData {
    key: string;
    lastModified: Date;
    data: GeoJSON.FeatureCollection;
  }

export type UpdateDataResponse = {
  dataLocs: {
    'mrms': {
      [dataType: string]: string[];
    };
  };
};

  