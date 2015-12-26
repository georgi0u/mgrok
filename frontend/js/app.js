(function() {
  var georgesListApp = angular.module('GeorgesListApp', []);

  var zeroOutTime = function(date) {
    date.setHours(0);
    date.setMinutes(0);
    date.setSeconds(0);
    date.setMilliseconds(0);
    return date;
  };

  var TheListController = function($scope, $http) {
    this.$scope = $scope;

    // Get Venue Data
    $http.get("/js/the_raw_list.js").then(
      function(response) {
        var data = response.data;
        // Add venue data to the scope
        $scope['venueData'] = response.data;

        // Add sorted venue names to the scope
        var venueNames = [];
        for (index in data) {
          venueNames.push(index);
        }
        venueNames.sort(function (a, b) {
          a = a.toLowerCase().replace(/^the /, '');
          b = b.toLowerCase().replace(/^the /, '');
          return a > b ? 1 : -1;
        });
        $scope['venueNames'] = venueNames;

        // Add a convenience array of the events to the scope
        $scope['eventList'] = [];
        for (index in $scope['venueData']) {
          var events = $scope['venueData'][index];
          $scope['eventList'] = $scope['eventList'].concat(events);
        }
        $scope['eventList'].forEach(function(event) {
          event.show = true;
        });
      },
      function(response) {
        $scope['error'] = 'Something is messed up. Sorry.';
      });
  };

  TheListController.prototype.getEventsToShow = function(venueName) {
    var events = this.$scope['venueData'][venueName];
    return events.filter(function(event) { return event.show; });
  };

  TheListController.prototype.showToday = function() {
    var today = zeroOutTime(new Date());
    this.$scope['eventList'].forEach(function(event) {
      var eventDate = zeroOutTime(new Date(event.date));
      event.show = (eventDate.getTime() == today.getTime());
    });
  };

  TheListController.prototype.showNext = function() {
    this.$scope['venueNames'].forEach(function(venueName) {
      var events = this.$scope['venueData'][venueName];
      events.forEach(function(event) {
        event.show = false;
      });
      events[0].show = true;
    }, this);
  };

  TheListController.prototype.showEverything = function() {
    this.$scope['eventList'].forEach(function(event) {
      event.show = true;
    });
  };

  TheListController.prototype.showWeekend = function() {
    var today = zeroOutTime(new Date());
    var dayOfWeek = today.getDay();

    this.$scope['eventList'].forEach(function(event) {
      event.show = true;
    });
  };

  georgesListApp.controller('TheListController', TheListController);

}());
