// Utility for displaying rank names based on title preference

/**
 * Get the appropriate rank name based on user's title preference
 * @param {Object} rank - The rank object with name and name_female properties
 * @param {string} titlePreference - 'male' or 'female'
 * @returns {string} The appropriate rank name
 */
export const getRankName = (rank, titlePreference = 'male') => {
  if (!rank) return '';
  
  if (titlePreference === 'female' && rank.name_female) {
    return rank.name_female;
  }
  return rank.name;
};

/**
 * Get both rank name variants for display
 * @param {Object} rank - The rank object
 * @returns {string} Combined rank name like "Squire / Lady"
 */
export const getRankNameBoth = (rank) => {
  if (!rank) return '';
  
  if (rank.name === rank.name_female) {
    return rank.name;
  }
  return `${rank.name} / ${rank.name_female}`;
};

export default { getRankName, getRankNameBoth };
