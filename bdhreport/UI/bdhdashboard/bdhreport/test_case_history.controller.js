sap.ui.controller("bdhreport.test_case_history", {
/**
* Called when a controller is instantiated and its View controls (if available) are already created.
* Can be used to modify the View before it is displayed, to bind event handlers and do other one-time initialization.
* @memberOf bdhreport.nightly_validation_report
*/	
	
	onInit: function() {
		var that = this;
		that.getView().addEventDelegate( 
				{
					onBeforeShow : function(evt) {
						var that = this;
						
						var oModel = new sap.ui.model.json.JSONModel();
					   	oModel.setProperty("/test_name", evt.data.dataList[0].test_name);	
						that.getView().byId('historyTitle').setModel(oModel);
						
						var oVizFrame = that.getView().byId("idVizFrame");
				    	oVizFrame.setVisible(true);
				        oVizFrame.setVizProperties({
				            legend: {
				                title: {
				                    visible: true
				                }
				            },
				            title: {
				                visible: false 
				            },
				            plotArea: {
		                        dataLabel: {
		                            visible: true
		                        }
		                    }
				        });
				        				        
				    	var dataModel = new sap.ui.model.json.JSONModel(evt.data);
				        oVizFrame.setModel(dataModel);
				        var oPopOver = that.getView().byId("idPopOver");
				        oPopOver.connect(oVizFrame.getVizUid());					        										
					}
				}, that);


	},
	
	getSplitContObj : function(){
		var result = this.getView().oParent.oParent;
		if(!result){
			jQuery.sap.log.error("SplitApp object can't be found");
		}
		return result;
	},
	
	
	/**
	 * Updates the item count within the line item table's header
	 * @param {object} oEvent an event containing the total number of items in the list
	 * @private
	 */
	onUpdateFinished : function (oEvent) {
		var that = this;
//		var iTotalItems = oEvent.getParameter("total");
//		var oModel =  that.getView().byId('tableTitleNightly').getModel();			    	
//		oModel.setProperty("/totalCount", iTotalItems);	
	},
	
	goBackDBList:function(){
		if (catagory == "BDH Push Validation"){
			this.getSplitContObj().toDetail("case_detail_push");
		} 
		if (catagory == "BDH Nightly Validation"){
			this.getSplitContObj().toDetail("case_detail_nightly");
		}
		
	},
	
	
});