(function() {
  /////////////
  // Helpers //
  /////////////

  var zeroOutTime = function(date) {
    date.setHours(0);
    date.setMinutes(0);
    date.setSeconds(0);
    date.setMilliseconds(0);
    return date;
  };


  /////////////////
  // Controllers //
  /////////////////

  var TheListController = function($scope, $http, $filter) {
    var self = this;
    this.$scope = $scope;
    this.$filter = $filter;
    this.venueNames = [];

    // Get Venue Data
    $http.get("/js/the_raw_list.js").then(
      function(response) {
        // Add updated date
        $scope['lastUpdated'] = response.data.updated;

        // Add venue data to the scope
        var shows = response.data.shows;
        $scope['venueData'] = shows;

        // Add sorted venue names to the scope
        self.venueNames = [];
        angular.forEach(shows, function(events, venueName) {
          self.venueNames.push(venueName);
        });
        self.venueNames.sort(function (a, b) {
          a = a.toLowerCase().replace(/^the /, '');
          b = b.toLowerCase().replace(/^the /, '');
          return a > b ? 1 : -1;
        });
        $scope['venueNames'] = angular.copy(self.venueNames);

        // Add a convenience array of the events to the scope
        $scope['eventList'] = [];
        angular.forEach($scope['venueData'], function(events, venueName) {
          $scope['eventList'] = $scope['eventList'].concat(events);
        });
        self.showToday(0);
      },
      function(response) {
        $scope['error'] = 'Something is messed up. Sorry.';
      });
  };

  TheListController.prototype.alreadyHappened = function(event) {
    var today = zeroOutTime(new Date());
    var eventDate = zeroOutTime(new Date(event.date));
    var eventInThePast = (eventDate.getTime() < today.getTime());
    return eventInThePast;
  };

  TheListController.prototype.defaultDateFilter = function(date) {
    return this.$filter('date')(date, 'EEE, MMM d @ h:mm a');
  };


  TheListController.prototype.getEventsToShow = function(venueName) {
    var events = this.$scope['venueData'][venueName];
    return events.filter(function(event) { return event.show; });
  };


  TheListController.prototype.showToday = function(index) {
    var todayStart = new Date();
    todayStart.setHours(7);
    var todayEnd = new Date();
    todayEnd.setDate(todayEnd.getDate() + 1);
    todayEnd.setHours(4);

    this.$scope['eventList'].forEach(function(event) {
      var eventDate = new Date(event.date);
      event.show = (
          eventDate.getTime() >= todayStart.getTime() &&
          eventDate.getTime() <= todayEnd.getTime());
    });
    var self = this;
    this.$scope['filterDate'] = function(date) {
      return self.$filter('date')(date, 'EEEE @ h:mm a');
    };
    this.$scope['selectedLink'] = index;
  };

  /**
   * TODO: factor out filtering events by date range
   */
  TheListController.prototype.showTomorrow = function(index) {
    var tomorrowStart = new Date();
    tomorrowStart.setDate(tomorrowStart.getDate() + 1);
    tomorrowStart.setHours(7);
    var tomorrowEnd = new Date();
    tomorrowEnd.setDate(tomorrowEnd.getDate() + 2);
    tomorrowEnd.setHours(4);

    this.$scope['eventList'].forEach(function(event) {
      var eventDate = new Date(event.date);
      event.show = (
          eventDate.getTime() >= tomorrowStart.getTime() &&
          eventDate.getTime() <= tomorrowEnd.getTime());
    });

    var self = this;
    this.$scope['filterDate'] = function(date) {
      return self.$filter('date')(date, 'EEEE @ h:mm a');
    };
    this.$scope['selectedLink'] = index;
  };


  TheListController.prototype.showNext = function(index) {

    this.$scope['venueNames'].forEach(function(venueName) {
      var events = this.$scope['venueData'][venueName];
      var foundNextEvent = false;
      events.forEach(function(event) {
        if (this.alreadyHappened(event) || foundNextEvent) {
          event.show = false;
        } else {
          event.show = true;
          foundNextEvent = true;
        }
      }, this);
    }, this);
    this.$scope['filterDate'] = this.defaultDateFilter.bind(this);
    this.$scope['selectedLink'] = index;
  };


  TheListController.prototype.showEverything = function(index) {
    this.$scope['eventList'].forEach(function(event) {
      event.show = true;
    });
    this.$scope['filterDate'] = this.defaultDateFilter.bind(this);
    this.$scope['selectedLink'] = index;
  };


  TheListController.prototype.showWeekend = function(index) {
    var today = zeroOutTime(new Date());
    var daysToThursday = 4 - today.getDay();
    var thursdayDate = new Date(today);
    thursdayDate.setDate(today.getDate() + daysToThursday);
    var daysToSaturday = 6 - today.getDay();
    var sundayDate = new Date(today);
    sundayDate.setDate(today.getDate() + daysToSaturday + 1);
    sundayDate.setHours(23);
    sundayDate.setMinutes(59);
    sundayDate.setSeconds(59);

    this.$scope['eventList'].forEach(function(event) {
      var eventDate = new Date(event.date);
      event.show = (
          eventDate.getTime() >= thursdayDate.getTime()
          && eventDate.getTime() <= sundayDate.getTime());
    });

    var self = this;
    this.$scope['filterDate'] = function(date) {
      return self.$filter('date')(date, 'EEEE @ h:mm a');
    };
    this.$scope['selectedLink'] = index;
  };


  TheListController.prototype.showWorkWeek = function(index) {
    var today = zeroOutTime(new Date());
    var daysToMonday = 1 - today.getDay();
    var daysToThursday = 4 - today.getDay();
    if (today.getDay() >= 5 || today.getDay() == 0) {
        daysToMonday += 7;
        daysToThursday += 7;
    }
    var mondayDate = new Date(today);
    mondayDate.setDate(today.getDate() + daysToMonday);
    var thursdayDate = new Date(today);
    thursdayDate.setDate(today.getDate() + daysToThursday);
    thursdayDate.setHours(23);
    thursdayDate.setMinutes(59);
    thursdayDate.setSeconds(59);

    this.$scope['eventList'].forEach(function(event) {
      var eventDate = new Date(event.date);
      event.show = (
          eventDate.getTime() >= mondayDate.getTime()
          && eventDate.getTime() <= thursdayDate.getTime());
    });

    var self = this;
    this.$scope['filterDate'] = function(date) {
      return self.$filter('date')(date, 'EEEE @ h:mm a');
    };
    this.$scope['selectedLink'] = index;
  };


  TheListController.prototype.getEventClass = function(event) {
    var alreadyHappened = this.alreadyHappened(event);
    var contains_link = (event.event_link && event.event_link != '');

    return {
      contains_link: contains_link,
      does_not_contain_link: !contains_link,
      past: alreadyHappened
    };
  };

  TheListController.prototype.filterVenues = function(filterStr) {
    if (!filterStr) {
      this.$scope['venueNames'] = angular.copy(this.venueNames);
      return
    }
    
    var filteredVenueNames = [];
    var lowerCaseFilterName = filterStr.toLowerCase();
    this.$scope['venueNames'] = this.venueNames.filter(function(venueName) {
      var lowerCaseVenueName = venueName.toLowerCase();
      var noPunctuationLowerCaseVenueName =
          lowerCaseVenueName.replace(/[.,-\/#!$%\^&\*;:{}=\-_`~()]/g,"");
      var noPunctuationFilter =
          lowerCaseFilterName.replace(/[.,-\/#!$%\^&\*;:{}=\-_`~()]/g,"");
      return (noPunctuationLowerCaseVenueName.match(noPunctuationFilter) != null) 
    });
  };


  ////////////////
  // Directives //
  ////////////////

  var eventTitleTemplate =
    '  <h3 class="datetime"'+
    '      title="{{theListController.defaultDateFilter(event.date)}}">'+
    '  <span data-ng-if="theListController.alreadyHappened(event)">already happened on </span>{{filterDate(event.date)}}</h3>' +
    '  <div style="position: relative">' +
    '    <ul class="event-artists">' +
    '      <li class="artist" data-ng-repeat="artist in event.artists">{{artist}}</li>' +
    '    </ul>' +
    '    <p class="message" data-ng-transclude></p>' +
    '  </div>';

  var eventTitleDirective = function() {
    return {
      template: eventTitleTemplate,
      transclude: true
    };
  };


  ///////////////////
  // Angular Setup //
  ///////////////////

  angular
    .module('GeorgesListApp', [])
    .controller('TheListController', TheListController)
    .directive('eventTitle', eventTitleDirective);
}());


$(function() {
  var headerSpacer = $('<div>');
    headerSpacer.height($('#header').outerHeight(true));
  headerSpacer.insertAfter($('#header'));
});
