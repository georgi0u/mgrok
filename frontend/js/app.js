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

  var replaceNonAlphaNumChars = function(str) {
    return str.replace(/[.,-\/#!$%\^&\*;:{}=\-_`~()]/g, '');
  }


  /////////////////
  // Controllers //
  /////////////////

  var TheListController = function($scope, $http, $filter) {
    var self = this;
    this.$filter = $filter;
    this.venueNames = [];
    this.eventModel = {};

    $scope['eventModel'] = this.eventModel;

    // Get Venue Data
    $http.get('/js/the_raw_list.js').then(
      function(response) {
        // Add updated date
        self.eventModel['lastUpdated'] = response.data.updated;

        // Add venue data to the scope
        var shows = response.data.shows;
        self.eventModel['venueData'] = shows;

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
        self.eventModel['filteredVenues'] = angular.copy(self.venueNames);

        // Add a convenience array of the events to the scope
        self.eventModel['eventList'] = [];
        angular.forEach(
          self.eventModel['venueData'], function(events, venueName) {
            self.eventModel['eventList'] =
              self.eventModel['eventList'].concat(events);
          });
        self.showToday(0);
      },
      function(response) {
        self.eventModel['error'] = 'Something is messed up. Sorry.';
      });
    
    this.eventModel['showDeadVenues'] = true;
  };
  
  TheListController.prototype.alreadyHappened = function(event) {
    var today = zeroOutTime(new Date());
    var eventDate = zeroOutTime(new Date(event.date));
    var eventInThePast = (eventDate.getTime() < today.getTime());
    return eventInThePast;
  };

  TheListController.prototype.isVenueDead = function(venueName) {
    return !this.eventModel['venueData'][venueName].some(function(event) {
      return event.show;
    });
  };

  TheListController.prototype.getEventsToShow = function(venueName) {
    var events = this.eventModel['venueData'][venueName];
    return events.filter(function(event) { return event.show; });
  };

  TheListController.prototype.showBetweenDates =
    function(startDate, endDate, opt_dateFormat) {
      this.eventModel['eventList'].forEach(function(event) {
        var eventDate = new Date(event.date);
        event.show = (
          eventDate.getTime() >= startDate.getTime() &&
            eventDate.getTime() <= endDate.getTime());

      });
      
      var self = this;
      var dateFormat = (opt_dateFormat == undefined) ?
          'EEEE @ h:mm a' : opt_dateFormat;
      this.eventModel['filterDate'] = function(date) {
        return self.$filter('date')(date, dateFormat);
      };
    };

  TheListController.prototype.showToday = function() {
    var todayStart = new Date();
    todayStart.setHours(7);
    var todayEnd = new Date();
    todayEnd.setDate(todayEnd.getDate() + 1);
    todayEnd.setHours(4);
    this.showBetweenDates(todayStart, todayEnd);
  };

  TheListController.prototype.showTomorrow = function() {
    var tomorrowStart = new Date();
    tomorrowStart.setDate(tomorrowStart.getDate() + 1);
    tomorrowStart.setHours(7);
    var tomorrowEnd = new Date();
    tomorrowEnd.setDate(tomorrowEnd.getDate() + 2);
    tomorrowEnd.setHours(4);
    this.showBetweenDates(tomorrowStart, tomorrowEnd);
  };

  TheListController.prototype.showNext = function() {
    this.venueNames.forEach(function(venueName) {
      var events = this.eventModel['venueData'][venueName];
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
    var self = this;
    this.eventModel['filterDate'] = function(date) {
      return self.$filter('date')(date, 'EEE, MMM d @ h:mm a');
    };
  };

  TheListController.prototype.showWeekend = function() {
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
    this.showBetweenDates(thursdayDate, sundayDate);
  };

  TheListController.prototype.showWorkWeek = function() {
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
    this.showBetweenDates(mondayDate, thursdayDate);
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
  
  TheListController.prototype.filterVenuesByName = function() {
    var filterStr = this.eventModel['venueFilter'];
    if (!filterStr) {
      this.eventModel['filteredVenues'] = angular.copy(this.venueNames);
      return;
    }
    var filteredVenueNames = [];
    var lowerCaseFilterName = filterStr.toLowerCase();
    this.eventModel['filteredVenues'] = this.venueNames.filter(function(venueName) {
      var lowerCaseVenueName = venueName.toLowerCase();
      var noPunctuationLowerCaseVenueName =
          replaceNonAlphaNumChars(lowerCaseVenueName);
      var noPunctuationFilter =
          replaceNonAlphaNumChars(lowerCaseFilterName);
      return (noPunctuationLowerCaseVenueName.match(noPunctuationFilter) != null)
    });
  };


  ////////////////
  // Directives //
  ////////////////

  var eventTitleTemplate =
    '  <h3 class="datetime"' +
    '      title="{{event.date | date : \'EEE, MMM d @ h:mm a\'}}">'+
    '  <span data-ng-if="theListController.alreadyHappened(event)">already happened on </span>{{eventModel.filterDate(event.date)}}</h3>' +
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
  // Sticky header spacer
  var headerSpacer = $('<div>');
  headerSpacer.height($('#header').outerHeight(true));
  headerSpacer.insertAfter($('#header'));

  // Navigation link classes
  $('.selectable li').click(function(event) {
    $(this).siblings().removeClass('selected');
    $(this).addClass('selected');
  });

  // Dead venue button fade/toggle
  $('#dead-venue-filters li').click(function(event) {
    var sibling = $(this).siblings();
    $(this).fadeOut(400, function() {
      sibling.show();
    });
  });
});
